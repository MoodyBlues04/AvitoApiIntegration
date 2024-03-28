from .google_sheets import GoogleSheetsApi
from .avito import AuthRequest, AvitoService, AvitoApi, AccountInfo


class AvitoSheetProcessor:
    ROW_LEN = 4
    ERR_COLUMN = 10
    STATUS_COLUMN = 5
    URL_COLUMN = 19

    def __init__(self, sheet_id: str, credentials_worksheet: str) -> None:
        self.__google_sheets_api = GoogleSheetsApi(sheet_id, credentials_worksheet)
        self.__credentials_worksheet = credentials_worksheet

    def execute(self):
        all_rows = self.__google_sheets_api.get_all_rows()

        for row_index, row in enumerate(all_rows):
            try:
                if row_index == 0 or len(row) > 0 and not row[0]:
                    continue
                if len(row) < self.ROW_LEN:
                    print('Sheet finished')
                    break

                profile_id, client_id, client_secret = row[1:4]
                print(f'{row_index+1}. Processing profile: {profile_id} {client_id} {client_secret}')

                auth_request = AuthRequest(client_id.strip(), client_secret.strip())
                try:
                    avito_service = AvitoService(auth_request)
                except Exception:
                    self.__set_status(row_index + 1, 'BLOCK')
                    print('Profile blocked')
                    continue
                print('Avito api authorized. Profile active')

                self.__set_account_info(row_index, avito_service.get_account_info())
                print('Account data updated')

                ads_stat_by_region = avito_service.get_ads_stat_by_regions()
                self.__update_ads_stat(profile_id, ads_stat_by_region)
                print('Ads stats updated')

                avito_service.answer_on_reviews()
                print('Reviews answered')

                # TODO cannot check if it works - no operations on test account
                # operations_history = avito_service.api.get_month_operations_history()['result']['operations']
                # self.__set_operation_history(profile_id, operations_history)
                # print('Balance stats updated')
            except Exception as e:
                self.__log_error(e, row_index)

    def __set_account_info(self, row_index: int, account_info: AccountInfo) -> None:
        self.__google_sheets_api.set_values((row_index + 1, self.STATUS_COLUMN), [account_info.get_ads_data()])
        self.__google_sheets_api.set_values((row_index + 1, self.URL_COLUMN), [account_info.get_account_data()])

    def __update_ads_stat(self, profile_id: str, ads_stat: dict) -> None:
        self.__google_sheets_api.set_worksheet(f'{profile_id} | Стата')
        row_index = self.__google_sheets_api.get_first_empty_row()

        try:
            current_data = self.__google_sheets_api.get_values((2, 1), (row_index, 5))
        except Exception:
            current_data = []

        for region, stat in ads_stat.items():
            updated = False
            data_to_add = [
                str(stat['date']),
                region,
                stat['active_count'],
                stat['unique_views'],
                stat['unique_contacts']
            ]
            for data_row_index, row in enumerate(current_data):
                if row[1].strip() == region and row[0].strip() == str(stat['date']):
                    current_data[data_row_index] = data_to_add
                    updated = True
                    break
            if not updated:
                current_data.append(data_to_add)

        self.__google_sheets_api.set_values((2, 1), current_data)

    def __set_operation_history(self, profile_id: str, operation_history: list) -> None:
        self.__google_sheets_api.set_worksheet(f'{profile_id} | Стата')
        row_index = self.__google_sheets_api.get_first_empty_row()
        for operation in operation_history:
            self.__google_sheets_api.set_values((row_index, 7), [[
                operation['updatedAt'],
                operation['operationType'],
                operation['amountTotal'],
                operation['serviceName'],
                operation['itemId']
            ]])


    def __log_error(self, e: Exception, row_index: int) -> None:
        raise e
        # self.__google_sheets_api.set_value((row_index + 1, self.ERR_COLUMN), str(e))

    def __set_status(self, row_index: int, status: str) -> None:
        self.__google_sheets_api.set_value((row_index + 1, self.STATUS_COLUMN), status)
