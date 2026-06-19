import pandas as pd


class DataCleaner:
    # All columns produced by the full pipeline
    SOCIAL_COLUMNS = [
        "Facebook URL", "Instagram URL", "Twitter URL",
        "LinkedIn URL", "YouTube URL", "Wikipedia URL", "TripAdvisor URL",
    ]

    @staticmethod
    def clean_data(raw_data):
        """
        Cleans and structures raw data collected from scrapers.
        - Removes duplicates
        - Normalises missing values for all known columns
        """
        if not raw_data:
            return pd.DataFrame()

        df = pd.DataFrame(raw_data)

        # Remove duplicates based on Business Name and Location
        if "Business Name" in df.columns and "Location" in df.columns:
            df.drop_duplicates(subset=["Business Name", "Location"], keep="first", inplace=True)

        # Columns to fill with empty string when null/missing
        fill_cols = [
            "Website URL", "Phone Number", "Email Address",
            "Google Maps Profile Link",
            "Discovery Method", "Confidence Score", "Validation Signals",
            "Search Query Used", "Discovery Status",
        ] + DataCleaner.SOCIAL_COLUMNS

        for col in fill_cols:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
                # Treat "None" / "nan" string values as empty
                df[col] = df[col].replace({"None": "", "nan": ""})
            else:
                df[col] = ""

        return df

    @staticmethod
    def classify_digital_opportunity(website_status):
        """
        LEGACY helper — kept for backward compatibility.
        The main pipeline now uses OnlinePresenceScorer.opportunity_to_priority()
        which uses the full multi-signal Opportunity Score.

        'No Website'   → High
        'Has Website'  → Medium  (URL listed but unverifiable)
        'Poor Website' → Medium
        'Good Website' → Low
        """
        if website_status == "No Website":
            return "High"
        elif website_status in ("Poor Website", "Has Website"):
            return "Medium"
        else:
            return "Low"


if __name__ == "__main__":
    sample_data = [
        {"Business Name": "A", "Location": "X", "Website URL": None},
        {"Business Name": "A", "Location": "X", "Website URL": None},  # duplicate
    ]
    df = DataCleaner.clean_data(sample_data)
    print(df)
