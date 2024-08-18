import json
import os
import logging
import pymysql
import boto3
from typing import Dict
from botocore.exceptions import ClientError
import bcrypt
from shared.database_manager import DatabaseConfig

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,PATCH',
}

def lambda_handler(event, context):
    if event['httpMethod'] == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({
                "message": "CORS Preflight Response OK"
            })
        }

    error_message = 'Error : %s'
    error_500 = {
        "statusCode": 500,
        "headers": cors_headers,
        "body": json.dumps({
            "error": "Internal Error - User Not Updated"
        })
    }
    required_cognito_groups = ['admin', 'user']
    cognito_groups = 'cognito:groups'

    try:

        user = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_cognito_groups = user.get(cognito_groups, '').split(',') if isinstance(user.get(cognito_groups), str) \
            else user.get(cognito_groups, [])

        if user.get(cognito_groups) is None or not any(
                group in required_cognito_groups for group in user_cognito_groups):
            return {
                "statusCode": 403,
                "headers": cors_headers,
                "body": json.dumps({
                    "message": "Forbidden"
                }),
            }

        json_body = json.loads(event['body'])
        username = json_body['username']
        old_password = json_body['old_password']
        new_password = json_body['new_password']

        if username is None or old_password is None or new_password is None:
            raise ValueError("Bad request - Parameters are missing")

        return update_user_password_patch(username, old_password, new_password)

    except KeyError as e:
        logging.error(error_message, e)
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps({
                "error": "Bad request - Invalid request format"
            })
        }

    except ValueError as e:
        logging.error(error_message, e)
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps({
                "error": str(e)
            })
        }

    except ClientError as e:
        logging.error('Error AWS ClientError : %s', e)
        return error_500

    except pymysql.MySQLError as e:
        logging.error('Error MySQL : %s', e)
        return error_500

    except Exception as e:
        logging.error(error_message, e)
        return error_500


def update_user_password_patch(username, old_password, new_password):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            search_query_username = "SELECT * FROM Users WHERE username = %s"
            cursor.execute(search_query_username, username)
            result_username = cursor.fetchall()

            if len(result_username) > 0:

                user = result_username[0]
                stored_password_hash = user['password']

                confirm_old_password = bcrypt.checkpw(old_password.encode('utf-8'),
                                                      stored_password_hash.encode('utf-8'))

                if confirm_old_password:

                    try:
                        secret_name = os.getenv("SECRET_NAME")
                        region_name = os.getenv("REGION_NAME")
                        secrets = get_secret(secret_name, region_name)
                        client = boto3.client('cognito-idp', region_name=region_name)
                        user_pool_id = secrets['USER_POOL_ID']
                        client_id = secrets['CLIENT_ID']

                        response = client.admin_initiate_auth(
                            UserPoolId=user_pool_id,
                            ClientId=client_id,
                            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                            AuthParameters={
                                'USERNAME': username,
                                'PASSWORD': old_password
                            }
                        )

                        if 'AuthenticationResult' in response:
                            client.admin_set_user_password(
                                UserPoolId=user_pool_id,
                                Username=username,
                                Password=new_password,
                                Permanent=True
                            )

                            salt = bcrypt.gensalt()
                            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)

                            update_query = "UPDATE Users SET password=%s WHERE username = %s"
                            cursor.execute(update_query, (hashed_password.decode('utf-8'), username))
                            connection.commit()
                            return {
                                "statusCode": 200,
                                "headers": cors_headers,
                                "body": json.dumps({
                                    "message": "User Updated Successfully"
                                }),
                            }
                        else:
                            raise ValueError("Unexpected Challenge")

                    except ClientError as e:
                        logging.error('Error AWS ClientError : %s ', e)
                        raise e
                    except Exception as e:
                        logging.error('Error : %s', e)
                        raise e
                else:
                    raise ValueError("Bad request - Invalid temp_password")
            else:
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "User Not Found"
                    }),
                }
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
