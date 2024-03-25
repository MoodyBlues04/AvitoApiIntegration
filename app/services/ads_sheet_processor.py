from .google_sheets import GoogleSheetsApi
from .avito import AuthRequest, AvitoService, AvitoApi, AccountInfo


class AvitoSheetProcessor:
    ROW_LEN = 4
    ERR_COLUMN = 10
    STATUS_COLUMN = 5
    URL_COLUMN = 19

    def __init__(self, sheet_id: str, credentials_worksheet: str, ads_worksheet: str) -> None:
        self.__google_sheets_api = GoogleSheetsApi(sheet_id, credentials_worksheet)
        self.__credentials_worksheet = credentials_worksheet
        self.__ads_worksheet = ads_worksheet

    def execute(self):
        all_rows = self.__google_sheets_api.get_all_rows()

        for row_index, row in enumerate(all_rows):
            try:
                if row_index == 0 or len(row) > 0 and not row[0]:
                    continue
                if len(row) < self.ROW_LEN:
                    raise Exception('Incorrect args count')

                profile_id, client_id, client_secret = row[1:4]

                auth_request = AuthRequest(client_id.strip(), client_secret.strip())
                try:
                    avito_service = AvitoService(auth_request)
                except Exception:
                    self.__set_status(row_index + 1, 'BLOCK')
                    continue

                self.__set_account_info(row_index, avito_service.get_account_info())

                # self.__google_sheets_api.set_worksheet(f'{profile_id} | Стата')
                #     4) статистика
                #     5) статистика по балансу и по объявлениям
                #     6) пишем в конец листа (проверим что не было такого ранее)

                avito_service.answer_on_reviews()

            #     7) по списку отзывов автоответ (шаблоны дадут) + добавляем в конец строки статус "отвечено"

            except Exception as e:
                self.__log_error(e, row_index)

    def __set_account_info(self, row_index: int, account_info: AccountInfo) -> None:
        self.__google_sheets_api.set_values((row_index + 1, self.STATUS_COLUMN), [account_info.get_ads_data()])
        self.__google_sheets_api.set_values((row_index + 1, self.URL_COLUMN), [account_info.get_account_data()])

    def __log_error(self, e: Exception, row_index: int) -> None:
        raise e
        # self.__google_sheets_api.set_value((row_index + 1, self.ERR_COLUMN), str(e))

    def __set_status(self, row_index: int, status: str) -> None:
        self.__google_sheets_api.set_value((row_index + 1, self.STATUS_COLUMN), status)
