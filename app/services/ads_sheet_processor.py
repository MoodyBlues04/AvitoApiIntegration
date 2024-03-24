from .google_sheets import GoogleSheetsApi
from .avito import AvitoApi, AuthRequest


class AvitoSheetProcessor:
    ROW_LEN = 4
    ERR_COLUMN = 10

    def __init__(self, sheet_id: str, credentials_worksheet: str, ads_worksheet: str) -> None:
        self.__google_sheets_api = GoogleSheetsApi(sheet_id, credentials_worksheet)
        self.__credentials_worksheet = credentials_worksheet
        self.__ads_worksheet = ads_worksheet

    def execute(self):
        all_rows = self.__google_sheets_api.get_all_rows()

        for row_idx, row in enumerate(all_rows):
            try:
                if len(row) > 0 and not row[0]:
                    continue
                if len(row) < self.ROW_LEN:
                    raise Exception('Incorrect args count')

                profile_id, client_id, client_secret = row[1:4]

                auth_request = AuthRequest(client_id, client_secret)
                avito_api = AvitoApi(auth_request)

            #     1) acc data (balance, ads count, ads2 count, reviews count, rating, nearest ad,
            #           profile url and other profile data
            #     2) validate such response object and throw error on failed validation
            #     3) write to sheet

            #     4) статистика (переключаемся на отдельный лист)
            #     5) статистика по балансу и по объявлениям
            #     6) пишем в конец листа (проверим что не было такого ранее)

            #     7) по списку отзывов автоответ (шаблоны дадут) + добавляем в конец строки статус "отвечено"

            except Exception as e:
                self.__log_error(e, row_idx)

    def __log_error(self, e: Exception, row_index: int) -> None:
        self.__google_sheets_api.set_value((row_index + 1, self.ERR_COLUMN), str(e))
