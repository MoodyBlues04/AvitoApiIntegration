from __future__ import annotations
import requests


class AuthRequest:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self.__client_id = client_id
        self.__client_secret = client_secret

    def get_request(self) -> dict:
        return {
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
            'grant_type': 'client_credentials'
        }


class AvitoApi:
    API_HOST = 'https://api.avito.ru'
    AUTH_API_HOST = API_HOST + '/token'
    CORE_API_HOST = API_HOST + '/core/v1'
    RATINGS_API_HOST = API_HOST + '/ratings/v1'

    def __init__(self, auth_request: AuthRequest) -> None:
        self.__auth_headers = self.__get_auth_headers(auth_request.get_request())

    def get_account(self) -> dict:
        return self.__get(self.CORE_API_HOST + "accounts/self", headers=self.__auth_headers)

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
        access_token = self.__get_access_token(auth_data)
        return {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/122.0.0.0 Safari/537.36',
            'Authorization': f'Bearer {access_token}',
        }

    def __get_access_token(self, auth_data: dict):
        return self.__post(self.AUTH_API_HOST, data=auth_data).get('access_token')

    def __get(self, url: str, params: dict|None = None, headers: dict|None = None) -> dict:
        return self.__request('GET', url, params, headers)

    def __post(self, url: str, data: dict | None = None, headers: dict | None = None) -> dict:
        return self.__request('POST', url, data, headers)

    def __request(self, method: str, url: str, data: dict|None = None, headers: dict|None = None) -> dict:
        response = requests.request(method, url, data=data, headers=headers)
        response_data = response.json()
        if response.status_code != 200 or response_data.get('error') is not None:
            raise Exception(f'Request to `{url}` failed with response: `{response_data}`')
        return response_data
