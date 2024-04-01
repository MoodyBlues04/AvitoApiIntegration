import datetime
import argparse
from dotenv import load_dotenv
from app.services.ads_sheet_processor import AvitoSheetProcessor

load_dotenv()


SHEET_ID = '1UD2CutAVHMk6M6f1brt5XVLcdwofYT6a7Hcl20dVOUA'
WORKSHEET = 'test'

parser = argparse.ArgumentParser(description='Avito api integration')
parser.add_argument('days_to_load', type=int,
                    help="Count of days before today to load statistics to sheet")


def main():
    args = parser.parse_args()
    date_from = datetime.date.today() - datetime.timedelta(days=args.days_to_load)
    processor = AvitoSheetProcessor(SHEET_ID, WORKSHEET)
    processor.execute(date_from)


if __name__ == '__main__':
    main()

