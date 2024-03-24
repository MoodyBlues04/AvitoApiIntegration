import pygsheets
from os import getenv


class GoogleSheetsApi:
    def __init__(self, sheet_id: str, worksheet_title: str):
        service_file = getenv('GOOGLE_API_CREDENTIALS_PATH')
        self.__client = pygsheets.authorize(service_file=service_file)
        self.__sheet = self.__client.open_by_key(sheet_id)
        self.__worksheet = None
        self.set_worksheet(worksheet_title)

    def set_worksheet(self, title: str) -> None:
        try:
            self.__worksheet = self.__sheet.worksheet_by_title(title)
        except pygsheets.exceptions.WorksheetNotFound:
            self.__worksheet = self.__sheet.add_worksheet(title, rows=1000)

    def clear_worksheet(self, start: str|tuple) -> None:
        self.__worksheet.clear(start=start)

    def increase_rows_count(self, add_rows: int) -> None:
        self.__worksheet.add_rows(add_rows)

    def get_rows_count(self) -> int:
        return self.__worksheet.rows

    def add_rows(self, rows: list[list]) -> None:
        """ Adds rows at the bottom of existing rows """

        row_idx = self.get_first_empty_row()
        for row in rows:
            if row_idx % 10 == 0:
                print('Adding rows index:', row_idx)

            self.set_row(row_idx, row)
            row_idx += 1

    def set_value(self, addr: tuple|str, value) -> None:
        self.__worksheet.update_value(addr, value)

    def set_row(self, row: int, row_data: list) -> None:
        self.__worksheet.update_row(row, row_data)

    def is_set_row(self, row: int) -> bool:
        row_list = self.get_row(row)
        return len(row_list) > 0

    def get_all_rows(self, return_as: str = 'matrix') -> list[list]:
        return self.__worksheet.get_all_values(returnas=return_as, include_tailing_empty=False)

    def get_row(self, row: int, return_as: str = 'matrix') -> list:
        return self.__worksheet.get_row(row, returnas=return_as, include_tailing_empty=False)

    def get_first_empty_row(self, col: int = 1) -> int:
        col_data = self.get_col(col)
        return len(col_data) + 1

    def get_col(self, col: int, return_as: str = 'matrix'):
        return self.__worksheet.get_col(col, return_as, include_tailing_empty=False)

    def share(self, email_or_domain: str, role: str = 'reader', type: str = 'user') -> None:
        self.__sheet.share(email_or_domain, role=role, type=type)
