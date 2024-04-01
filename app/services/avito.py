from __future__ import annotations
import requests
import datetime
from time import sleep


class AuthRequest:
    GRANT_TYPE = 'client_credentials'

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.__client_id = client_id
        self.__client_secret = client_secret

    def get_request(self) -> dict:
        return {
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
            'grant_type': 'client_credentials'
        }


class AccountInfo:
    def __init__(self, status: str, balance: str, account: dict, ads: dict, reviews: int, rating: int, ad_min_date: datetime.date) -> None:
        self.status = status
        self.balance = balance
        self.account = account
        self.ads = ads
        self.reviews = reviews
        self.rating = rating
        self.ad_min_date = ad_min_date

    def get_ads_data(self) -> list:
        return [
            self.status,
            self.balance,
            self.ad_min_date,
            self.ads[AvitoApi.STATUS_ACTIVE],
            self.ads[AvitoApi.STATUS_REJECTED],
            self.reviews,
            self.rating,
        ]

    def get_account_data(self) -> list:
        return [
            self.account['profile_url'],
            self.account['name'],
            self.account['id'],
            self.account['email'],
            self.account['phone'],
        ]


class AvitoService:
    DEFAULT_MESSAGE_TEXT = 'Спасибо за Ваш отзыв!'

    def __init__(self, auth_request: AuthRequest) -> None:
        self.__api = AvitoApi(auth_request)

    @property
    def api(self) -> AvitoApi:
        return self.__api

    def get_account_info(self, date_from: datetime.date) -> AccountInfo:
        account = self.__api.get_account()
        balance = self.__api.get_account_balance(account['id'])
        ads_ids = self.__api.get_ads_ids(AvitoApi.STATUS_ACTIVE)
        ads_stat = self.__get_ads_statistics(account['id'], ads_ids, date_from)
        ads_count = {ad_status: self.__api.get_ads_count(ad_status) for ad_status in AvitoApi.ADS_STATUSES}

        return AccountInfo(
            'active',
            balance['real'],
            account,
            ads_count,
            self.__api.get_reviews().get('total'),
            self.__api.get_ratings().get('rating', dict()).get('score', 0),
            self.__get_min_ads_date(ads_stat)
        )

    def answer_on_reviews(self, message: str = DEFAULT_MESSAGE_TEXT) -> None:
        reviews_to_answer = self.get_not_answered_reviews_ids()
        for review_id in reviews_to_answer:
            self.__api.answer_on_review(review_id, message)

    def get_not_answered_reviews_ids(self) -> list:
        not_answered_reviews = filter(lambda el: not el.get('answer'), self.__api.get_all_reviews())
        return list(map(lambda el: el['id'], not_answered_reviews))

    def get_ads_stat_by_regions(self, date_from: datetime.datetime):
        account = self.__api.get_account()
        account_id = account['id']
        ads_ids = self.__api.get_ads_ids(AvitoApi.STATUS_ACTIVE)
        ads_stat = self.__get_ads_statistics(account_id, ads_ids, date_from)

        ads_stat_by_region = dict()
        today = datetime.date.today()
        for ad_stat in ads_stat:
            ad_info = self.__api.get_ad(account_id, ad_stat['itemId'])
            region = ad_info['url'].split('/')[3]
            if ads_stat_by_region.get(region) is None:
                ads_stat_by_region[region] = {'unique_views': 0, 'unique_contacts': 0, 'active_count': 0, 'date': today}
            ads_stat_by_region[region]['unique_views'] += sum(stat.get('uniqViews', 0) for stat in ad_stat['stats'])
            ads_stat_by_region[region]['unique_contacts'] += sum(stat.get('uniqContacts', 0) for stat in ad_stat['stats'])
            ads_stat_by_region[region]['active_count'] += int(ad_info['status'] == AvitoApi.STATUS_ACTIVE)

        return ads_stat_by_region

    def __get_min_ads_date(self, ads_stat: list[dict]) -> datetime.date:
        min_date = None
        for ad_stat in ads_stat:
            for stat in ad_stat['stats']:
                date = stat.get('date')
                if date is not None and (min_date is None or min_date > date):
                    min_date = date
        return min_date

    def __get_ads_statistics(
            self,
            user_id: str,
            ads_ids: list,
            date_from: datetime.date,
            date_to: datetime.date = datetime.date.today()) -> list:
        stat = []
        for chunk in chunks(ads_ids, 200):
            stat += self.__api.get_ads_stat(user_id, chunk, date_from, date_to)['result']['items']
            sleep(2)
        return stat


class AvitoApi:
    API_HOST = 'https://api.avito.ru'
    AUTH_API_HOST = API_HOST + '/token'
    CORE_API_HOST = API_HOST + '/core/v1'
    RATINGS_API_HOST = API_HOST + '/ratings/v1'
    STAT_API_HOST = API_HOST + '/stats/v1'

    STATUS_ACTIVE = 'active'
    STATUS_REJECTED = 'rejected'
    ADS_STATUSES = [STATUS_ACTIVE, STATUS_REJECTED]

    __auth_headers: dict|None = None

    def __init__(self, auth_request: AuthRequest) -> None:
        self.__auth_headers = self.__get_auth_headers(auth_request.get_request())

    def get_account(self) -> dict:
        return self.__get(self.CORE_API_HOST + '/accounts/self')

    def get_account_balance(self, user_id: str) -> dict:
        return self.__get(self.CORE_API_HOST + f'/accounts/{user_id}/balance/')

    def get_ad(self, user_id: str, ad_id: int|str) -> dict:
        return self.__get(self.CORE_API_HOST + f'/accounts/{user_id}/items/{ad_id}')

    def get_ads_count(self, status: str = 'active') -> int:
        return len(self.get_all_ads(status))

    def get_ads_ids(self, status: str = 'active') -> list:
        return list(map(lambda ad: ad['id'], self.get_all_ads(status)))

    def get_all_ads(self, status: str = 'active') -> list[dict]:
        page = 1
        ads = []
        while True:
            response = self.get_ads(status, page)
            if not response.get('resources'):
                break
            ads += response['resources']
            page += 1
        return ads

    def get_ads(self, status: str, page: int = 0) -> dict:
        return self.__get(self.CORE_API_HOST + f'/items?per_page=100&page={page}&status={status}')

    def get_ads_stat(self, user_id: str, ads_ids: list, date_from: datetime.date, date_to: datetime.date) -> dict:
        request = {
            'dateFrom': f'{date_from}',
            'dateTo': f'{date_to}',
            'itemIds': ads_ids,
            'periodGrouping': 'day'
        }
        headers = {'Content-type': 'application/json'}
        return self.__post(self.STAT_API_HOST + f'/accounts/{user_id}/items', json=request, headers=headers)

    def get_all_reviews(self) -> list:
        reviews = []
        offset = 0
        while True:
            new_reviews = self.get_reviews(offset)
            if not new_reviews.get('reviews'):
                break
            reviews += new_reviews['reviews']
            offset += 50
        return reviews

    def get_reviews(self, offset: int = 0) -> dict:
        return self.__get(self.RATINGS_API_HOST + f'/reviews?offset={offset}&limit=50')

    def answer_on_review(self, review_id: int|str, message: str) -> None:
        request = {
            'message': message,
            'reviewId': review_id
        }
        self.__post(self.RATINGS_API_HOST + '/answers', json=request)

    def get_ratings(self) -> dict:
        return self.__get(self.RATINGS_API_HOST + f'/info')

    def get_month_operations_history(self) -> dict:
        month_ago = (datetime.datetime.today() - datetime.timedelta(days=30))
        today = datetime.datetime.now()
        return self.get_operations_history(month_ago, today)

    def get_operations_history(self, date_from: datetime.datetime, date_to: datetime.datetime) -> dict:
        request = {
            'dateTimeFrom': date_from.strftime('%Y-%m-%dT%H:%M:%S'),
            'dateTimeTo': date_to.strftime('%Y-%m-%dT%H:%M:%S')
        }
        return self.__post(
            self.CORE_API_HOST + '/accounts/operations_history/',
            json=request,
            headers={'Content-type': 'application/json'}
        )

    def __get_auth_headers(self, auth_data: dict) -> dict:
        return {
            'Authorization': f'Bearer {self.__get_access_token(auth_data).strip()}',
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/122.0.0.0 Safari/537.36',
        }

    def __get_access_token(self, auth_data: dict) -> str:
        response = self.__post(self.AUTH_API_HOST, data=auth_data)
        return response.get('access_token')

    def __get(self, url: str, params: dict|None = None, headers: dict|None = None) -> dict:
        return self.__request('GET', url, params, headers)

    def __post(self, url: str, data: dict|str|None = None, json: dict|None = None, headers: dict | None = None) -> dict:
        return self.__request('POST', url, headers=headers, data=data, json=json)

    def __request(self, method: str, url: str, data: dict|None = None, json: dict|None = None, headers: dict|None = None) -> dict:
        request_headers = dict()
        request_headers = self.__merge_dicts(request_headers, headers)
        request_headers = self.__merge_dicts(request_headers, self.__auth_headers)

        response = requests.request(method, url, headers=request_headers, data=data, json=json)
        response_data = response.json()
        if response.status_code != 200 or response_data.get('error') is not None:
            raise Exception(f'Request to `{url}` failed with response: `{response_data}`')
        return response_data

    def __merge_dicts(self, first: dict, second: dict|None):
        if second is not None:
            return {**first, **second}
        return first


def chunks(arr: list, chunk_size: int) -> list[list]:
    for i in range(0, len(arr), chunk_size):
        yield arr[i:i + chunk_size]
