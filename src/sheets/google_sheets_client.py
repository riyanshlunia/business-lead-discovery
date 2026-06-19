import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSheetsClient:
    def __init__(self):
        self.credentials_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
        self.credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]

        if self.credentials_json:
            try:
                credentials_info = json.loads(self.credentials_json)
                self.client = gspread.service_account_from_dict(credentials_info)
            except Exception:
                try:
                    credentials_info = json.loads(self.credentials_json)
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(
                        credentials_info, self.scope
                    )
                    self.client = gspread.authorize(creds)
                except Exception as e:
                    self.client = None
                    print(f"Warning: Invalid Google Sheets credentials JSON in env var: {e}")
        elif os.path.exists(self.credentials_file):
            try:
                # Modern gspread ≥ 6: use service_account()
                self.client = gspread.service_account(filename=self.credentials_file)
            except Exception:
                # Fallback for older gspread versions
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    self.credentials_file, self.scope
                )
                self.client = gspread.authorize(creds)
        else:
            self.client = None
            print(
                "Warning: Google Sheets credentials not found in GOOGLE_SHEETS_CREDENTIALS_JSON "
                "or credentials file. Operating in mock mode."
            )

    def export_to_sheet(self, dataframe):
        """
        Exports the pandas DataFrame to the specified Google Sheet.
        Clears the existing content and rewrites from cell A1.
        """
        if not self.client or not self.sheet_id:
            print("Mock mode: Data to be written to Google Sheets:")
            print(dataframe.to_string())
            print(
                "\nTo enable actual Google Sheets integration, "
                "provide GOOGLE_SHEETS_CREDENTIALS_JSON and GOOGLE_SHEET_ID in .env"
            )
            return False

        try:
            sheet = self.client.open_by_key(self.sheet_id).sheet1

            # Clear existing data
            sheet.clear()

            # Build rows: header + data rows; convert every value to a plain
            # Python type that the Sheets API accepts (str/int/float/bool).
            def _safe(v):
                if v is None:
                    return ""
                if isinstance(v, float):
                    # NaN / Inf are not JSON-serialisable
                    import math
                    if math.isnan(v) or math.isinf(v):
                        return ""
                    return v
                if isinstance(v, (int, bool)):
                    return v
                return str(v)

            header = dataframe.columns.values.tolist()
            rows = [
                [_safe(cell) for cell in row]
                for row in dataframe.fillna("").values.tolist()
            ]
            data_to_write = [header] + rows

            # update() requires an explicit range in modern gspread
            sheet.update(range_name="A1", values=data_to_write)

            print(f"Successfully exported {len(rows)} rows to Google Sheets.")
            return True

        except Exception as e:
            print(f"Error exporting to Google Sheets: {e}")
            raise
