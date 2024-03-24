from dotenv import load_dotenv
from app.services.google_sheets import GoogleSheetsApi
from datetime import datetime
from app.services.avito import AvitoApi, AuthRequest
from app.services.ads_sheet_processor import AvitoSheetProcessor

load_dotenv()


SHEET_ID = '1BT3meEC-dfHROMXp8zPScRPB3NEleOhFtNpgyHqH6Mw'
WORKSHEET = datetime.now().strftime('%Y-%m-%d')
WORKSHEET_ADS = WORKSHEET + '-ads'

CLIENT_ID = 'ergejgnrkeg'
CLIENT_SECRET = 'fh97wfr74ho'


def main():
    processor = AvitoSheetProcessor(SHEET_ID, WORKSHEET, WORKSHEET_ADS)
    processor.execute()


if __name__ == '__main__':
    main()

