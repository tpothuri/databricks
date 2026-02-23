import requests
import boto3
import os
import pandas as pd
import xml.etree.ElementTree as ET
from io import StringIO
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
BUCKET = os.getenv("BRONZE_BUCKET")
s3 = boto3.client('s3')

# Defined Sources
JSON_TESTING_URL = "https://opendata.ecdc.europa.eu/covid19/testing/json/"
XML_VACCINATION_URL = "https://opendata.ecdc.europa.eu/covid19/COVID-19_VC_data_from_September_2023/xml/data_v7.xml"

def upload_df_to_s3(df, domain, source_type):
    """Standardized uploader for converted CSVs."""
    if df.empty:
        print(f"No data to upload for {domain}")
        return

    timestamp = datetime.now().strftime("%Y%m%d")
    key = f"structured/covid_data/source_ecdc/eu_covid19_data_{domain}_{timestamp}.csv"
    
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    s3.put_object(Bucket=BUCKET, Key=key, Body=csv_buffer.getvalue())
    print(f"{domain} ({source_type}) uploaded to: {key}")

def process_testing_json():
    print("Fetching Testing JSON...")
    response = requests.get(JSON_TESTING_URL)
    if response.status_code == 200:
        # JSON usually comes in a list of dicts or a 'records' key
        data = response.json()
        df = pd.DataFrame(data)
        upload_df_to_s3(df, "testing", "json")
    else:
        print(f"Failed Testing JSON: {response.status_code}")

def process_vaccination_xml():
    print("Fetching Vaccination XML...")
    response = requests.get(XML_VACCINATION_URL)
    if response.status_code == 200:
        # Parse XML to DataFrame
        root = ET.fromstring(response.content)
        all_records = []
        for record in root:
            row = {field.tag: field.text for field in record}
            all_records.append(row)
        
        df = pd.DataFrame(all_records)
        upload_df_to_s3(df, "vaccination_v7", "xml")
    else:
        print(f"Failed Vaccination XML: {response.status_code}")

if __name__ == "__main__":
    print(f"Starting Mixed Format Ingestion...")
    process_testing_json()
    process_vaccination_xml()