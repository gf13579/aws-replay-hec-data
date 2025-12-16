# Splunk S3 Event Replay Lambda

## Overview

This project provides a Lambda-ready Python script to replay event data written to Amazon S3 by Splunk Edge/Ingest Processor into a target Splunk index via HTTP Event Collector (HEC).  This can be useful for scenarios such as compliance investigations or statistical analysis of historical event data.

The script reads newline-delimited JSON, gzipped, from S3, using a partitioned folder structure:

```none
<some_prefix>/year=yyyy/month=mm/day=dd/instanceId=<some_guid>/
```
    
`some_prefix` can represent a data source (e.g., sourcetype or index).`instanceId` is not important.

Events are filtered by a user-defined time range (ISO8601). These dates, along with all other configuration is controlled via environment variables.

---
## Local Testing

1. Clone the Repository

```sh
git clone <repo-url>
cd <repo-directory>
```
    
2. Install Python Dependencies
    
(Recommended: Use a virtual environment.)

```sh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```
    
3. Configure AWS Credentials

Ensure your AWS credentials are available (for S3 access). You can set these up with the AWS CLI:

```sh
aws configure
```

This will set your credentials in `~/.aws/credentials`.
    
4. Set Environment Variables

Copy `env.example` to `.env` and update values as required:

```sh
cp env.example .env
# Edit .env with your settings
```

Or, export variables manually:

```sh
export S3_BUCKET=some-bucket
export S3_PREFIX=some_sourcetype/
# ...etc.
```
    
5. Run the Script Locally

```sh
python main.py
```

---
## Packaging for Lambda

1. Run the Packaging Script

This will produce `lambda_deploy.zip` ready for upload.

```sh
bash package_for_lambda.sh
```
    
2. Deploy the Lambda

- In the AWS Lambda console, create a new function (Python 3.x).
- Upload `lambda_deploy.zip` as the code package.
- Set required environment variables in the Lambda configuration.

---
## IAM Permissions

Your Lambda execution role must have permissions to:

- Write logs to CloudWatch:

```json
{
    "Effect": "Allow",
    "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
    ],
    "Resource": "arn:aws:logs:*:*:*"
}
```
    
- Read from the S3 bucket:
```json
{
    "Effect": "Allow",
    "Action": [
    "s3:GetObject",
    "s3:ListBucket"
    ],
    "Resource": [
    "arn:aws:s3:::<your-bucket-name>",
    "arn:aws:s3:::<your-bucket-name>/*"
    ]
}
```
    

Replace `<your-bucket-name>` with your actual bucket (e.g., `gf-vz-dmx-poc-01`).

---
## Notes

- When restoring older data, make sure your destination index is configured accordingly to prevent immediate data aging or freezing.
- The folder structure in S3 should match:

```none
<any_prefix>/year=YYYY/month=MM/day=DD/instanceId=<any_guid>/
```
    
- Only files matching the configured prefix and time range will be processed.
- The Splunk HEC URL and token must be provided via environment variables.
- If you wish to test with different data sources, adjust the prefix and bucket variables accordingly.
---
## Future improvements

Batching events into larger payloads for the POST to HEC - rather than one event per POST - will greatly increase performance and should be fairly easy to implement

---
## Support

For questions, open an issue or submit a pull request.

---
