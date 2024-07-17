import json
import boto3
import os
import logging
from typing import Dict
from botocore.exceptions import ClientError


def lambda_handler(event, __):
    try:
        secret_name = os.getenv("SECRET_NAME")
        region_name = os.getenv("REGION_NAME")
        secrets = get_secret(secret_name, region_name)

        client = boto3.client('cognito-idp', region_name='us-east-1')
        client_id = secrets['CLIENT_ID']

        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')
        password = body_parameters.get('password')

        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )

        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']
        refresh_token = response['AuthenticationResult']['RefreshToken']

        user_groups = client.admin_list_groups_for_user(
            Username=username,
            UserPoolId='us-east-1_1oU0zkg6n'
        )

        role = None
        if user_groups['Groups']:
            role = user_groups['Groups'][0]['GroupName']

        return {
            'statusCode': 200,
            'body': json.dumps({
                'id_token': id_token,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'role': role
            })
        }

    except ClientError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({"error_message ": e.response['Error']['Message']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"error_message": str(e)})
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
