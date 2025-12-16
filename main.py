import boto3
import gzip
import json
import os
import io
import requests
from dateutil import parser
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# === GLOBAL CONFIGURATION ===
# Read from .env file
load_dotenv()

# --- Environment Variables ---
S3_BUCKET = os.getenv('S3_BUCKET')
S3_PREFIX = os.getenv('S3_PREFIX', '')  # e.g., 'vclog/'
SPLUNK_HEC_URL = os.getenv('SPLUNK_HEC_URL')
SPLUNK_HEC_TOKEN = os.getenv('SPLUNK_HEC_TOKEN')
SPLUNK_TARGET_INDEX = os.getenv('SPLUNK_TARGET_INDEX')
START_TIME = os.getenv('START_TIME')  # ISO8601 (e.g., '2025-12-16T00:00:00Z')
END_TIME = os.getenv('END_TIME')      # ISO8601 (e.g., '2025-12-16T23:59:59Z')

# --- Parse start and end times ---
start_dt = parser.isoparse(START_TIME)
end_dt = parser.isoparse(END_TIME)

# --- Initialize S3 client ---
s3 = boto3.client('s3')

def list_relevant_s3_keys(bucket, prefix, start_dt, end_dt):
    """
    List S3 keys falling within the date range, based on partitioned structure: 
    <sourcetype>/year=YYYY/month=MM/day=DD/...
    """
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            parts = key.split('/')
            if len(parts) < 4:
                continue
            try:
                year = int(parts[1].split('=')[1])
                month = int(parts[2].split('=')[1])
                day = int(parts[3].split('=')[1])
                file_dt = datetime(year, month, day)
                if start_dt.date() <= file_dt.date() <= end_dt.date():
                    yield key
            except Exception:
                continue

def send_to_hec(event, session):
    headers = {
        'Authorization': f'Splunk {SPLUNK_HEC_TOKEN}',
        'Content-Type': 'application/json'
    }
    event["index"] = SPLUNK_TARGET_INDEX
    resp = session.post(
        SPLUNK_HEC_URL,
        headers=headers,
        data=json.dumps(event),
        timeout=5,
        verify=False
    )
    resp.raise_for_status()

def process_file(bucket, key, start_dt, end_dt, session):
    obj = s3.get_object(Bucket=bucket, Key=key)
    with gzip.GzipFile(fileobj=io.BytesIO(obj['Body'].read()), mode='rb') as gzfile:
        for line in gzfile:
            try:
                event = json.loads(line.decode('utf-8'))
                # Fix: Make event_time offset-aware UTC
                event_time = datetime.fromtimestamp(float(event['time']), tz=timezone.utc)
                if start_dt <= event_time <= end_dt:
                    send_to_hec(event, session)
            except Exception as e:
                print(f"Failed to process event in {key}: {e}")


def main():
    keys = list(list_relevant_s3_keys(S3_BUCKET, S3_PREFIX, start_dt, end_dt))
    print(f"Found {len(keys)} files to process.")
    with requests.Session() as session:
        for key in keys:
            print(f"Processing {key}...")
            process_file(S3_BUCKET, key, start_dt, end_dt, session)

def lambda_handler(event, context):
    main()

if __name__ == '__main__':
    main()