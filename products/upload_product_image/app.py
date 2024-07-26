import json
import logging
import base64
import pymysql
from botocore.exceptions import ClientError
import boto3
from typing import Dict
import os
from shared.database_manager import DatabaseConfig


def lambda_handler(event, context):

    image_data = base64.b64decode(event['body']['image_data'])
    image_name = event['body']['image_name']
    object_key = "products/" + image_name

    region_name = os.environ.get('REGION_NAME')
    secret_name = os.environ.get('SECRET_NAME')

    secrets = get_secret(secret_name, region_name)

    bucket_name = secrets['bucket_name']

    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=object_key, Body=image_data)

    object_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{object_key}"

    return {
        "statusCode": 200,
        "body": json.dumps({
            "image_url": object_url
        })
    }


def get_secret(secret_name: str, region_name: str) -> Dict[str, str]:
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logging.error("Failed to retrieve secret: %s", e)
        raise e

    return json.loads(get_secret_value_response['SecretString'])
