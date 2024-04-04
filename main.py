from dotenv import load_dotenv
from app.services.ads_sheet_processor import AvitoSheetProcessor

load_dotenv()


SHEET_ID = '1UD2CutAVHMk6M6f1brt5XVLcdwofYT6a7Hcl20dVOUA'
WORKSHEET = 'test'


def main():
    processor = AvitoSheetProcessor(SHEET_ID, WORKSHEET)
    processor.execute()


if __name__ == '__main__':
    main()

