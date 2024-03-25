from __future__ import annotations
import requests


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


class AvitoService:
    def __init__(self, auth_request: AuthRequest) -> None:
        self.__api = AvitoApi(auth_request)

    def get_account_info(self) -> dict:
        return {
            # 'balance': self.__api.get_account_balance(),
            'account': self.__api.get_account(),
        }


class AvitoApi:
    API_HOST = 'https://api.avito.ru'
    AUTH_API_HOST = API_HOST + '/token'
    CORE_API_HOST = API_HOST + '/core/v1'
    RATINGS_API_HOST = API_HOST + '/ratings/v1'

    __auth_headers: dict|None = None

    def __init__(self, auth_request: AuthRequest) -> None:
        self.__auth_headers = self.__get_auth_headers(auth_request.get_request())

    def get_account(self) -> dict:
        return self.__get(self.CORE_API_HOST + "accounts/self")

    def get_account_balance(self, user_id: str) -> dict:
        return self.__get(self.CORE_API_HOST + f'/accounts/{user_id}/balance/')

    def get_ads_count(self) -> int:
        return len(self.get_ads())

    def get_ads(self, status='active') -> list[dict]:
        page = 1
        ads = []
        while True:
            response = self.__get(self.CORE_API_HOST + f'/items?per_page=100&page={page}&status={status}')
            items = response['resources']
            if not items:
                break

            ads += items
            page += 1

        return ads

    def get_reviews(self, offset: int = 0) -> dict:
        return self.__get(self.RATINGS_API_HOST + f'/reviews?offset={offset}&limit=50')

    def get_ratings(self) -> dict:
        return self.__get(self.RATINGS_API_HOST + f'/info')

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

    def __post(self, url: str, data: dict|str|None = None, headers: dict | None = None) -> dict:
        return self.__request('POST', url, headers=headers, data=data)

    def __request(self, method: str, url: str, data: dict|None = None, headers: dict|None = None) -> dict:
        request_headers = dict()
        request_headers = self.__merge_dicts(request_headers, headers)
        request_headers = self.__merge_dicts(request_headers, self.__auth_headers)

        response = requests.request(method, url, headers=request_headers, data=data)
        response_data = response.json()
        if response.status_code != 200 or response_data.get('error') is not None:
            raise Exception(f'Request to `{url}` failed with response: `{response_data}`')
        return response_data

    def __merge_dicts(self, first: dict, second: dict|None):
        if second is not None:
            return {**first, **second}
        return first

