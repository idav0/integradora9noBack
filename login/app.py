import json
import boto3
import os
import logging
from typing import Dict
from botocore.exceptions import ClientError
from datetime import date, datetime
from shared.database_manager import DatabaseConfig


def lambda_handler(event, __):
    error_message = 'Error : %s'
    try:
        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')
        password = body_parameters.get('password')

        if username is None or password is None:
            raise ValueError('Bad Request - Parameters are missing ')

        secret_name = os.getenv("SECRET_NAME")
        region_name = os.getenv("REGION_NAME")
        secrets = get_secret(secret_name, region_name)

        client = boto3.client('cognito-idp', region_name='us-east-1')
        client_id = secrets['CLIENT_ID']

        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )

        if 'AuthenticationResult' in response:

            id_token = response['AuthenticationResult']['IdToken']
            access_token = response['AuthenticationResult']['AccessToken']
            refresh_token = response['AuthenticationResult']['RefreshToken']

            user_groups = client.admin_list_groups_for_user(
                Username=username,
                UserPoolId=secrets['USER_POOL_ID']
            )

            role = None
            if user_groups['Groups']:
                role = user_groups['Groups'][0]['GroupName']

            user = get_user_by_username(username)

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'auth': {
                        'id_token': id_token,
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'role': role
                    },
                    'user': user
                })
            }

    except KeyError as e:
        logging.error(error_message, e)
        return {
            'statusCode': 400,
            'body': json.dumps({"error_message": "Bad request - Invalid request format"})
        }

    except ValueError as e:
        logging.error(error_message, e)
        return {
            'statusCode': 400,
            'body': json.dumps({"error_message": str(e)})
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


def get_user_by_username(username):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            get_query_email = "SELECT * FROM Users Where email = %s"
            cursor.execute(get_query_email, username)
            users_email = cursor.fetchall()

            get_query_username = "SELECT * FROM Users Where username = %s"
            cursor.execute(get_query_username, username)
            users_username = cursor.fetchall()

            if len(users_email) > 0 or len(users_username) > 0:

                users = users_email[0] if len(users_email) > 0 else users_username[0]

                for user in users:
                    for key, value in user.items():
                        if isinstance(value, (date, datetime)):
                            user[key] = value.isoformat()
                return users
            else:
                raise Exception("Internal Error - User not found")
    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e
    finally:
        connection.close()


def get_secret(secret_name: str, region_name: str) -> Dict[str, str]:
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logging.error("Failed to retrieve secret: %s", e)
        raise e

    return json.loads(get_secret_value_response['SecretString'])
