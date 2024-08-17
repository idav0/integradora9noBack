import json
import logging
import os
import random
import string
import pymysql
import boto3
from typing import Dict
from botocore.exceptions import ClientError
import bcrypt
from shared.database_manager import DatabaseConfig

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,GET',
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
            "error": "Internal Error - Admin Not Inserted"
        })
    }
    required_cognito_groups = ['admin']
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
        email = json_body['email']
        password = generate_temporary_password()
        name = json_body['name']
        lastname = json_body['lastname']
        birthdate = json_body['birthdate']
        gender = json_body['gender']
        type_user = 'admin'

        if (username is None or email is None or name is None or lastname is None
                or birthdate is None or gender is None):
            raise ValueError("Bad request - Parameters are missing")

        return insert_admin(username, email, password, name, lastname, birthdate, gender, type_user)

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


def insert_admin(username, email, password, name, lastname, birthdate, gender, type_user):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            search_query_email = "SELECT * FROM Users WHERE email = %s"
            cursor.execute(search_query_email, email)
            result_email = cursor.fetchall()

            if len(result_email) == 0:
                search_query_username = "SELECT * FROM Users WHERE username = %s"
                cursor.execute(search_query_username, username)
                result_username = cursor.fetchall()

                if len(result_username) == 0:

                    try:
                        secret_name = os.getenv("SECRET_NAME")
                        region_name = os.getenv("REGION_NAME")
                        secrets = get_secret(secret_name, region_name)
                        client = boto3.client('cognito-idp', region_name=region_name)
                        user_pool_id = secrets['USER_POOL_ID']

                        client.admin_create_user(
                            UserPoolId=user_pool_id,
                            Username=username,
                            UserAttributes=[
                                {'Name': 'email', 'Value': email},
                                {'Name': 'email_verified', 'Value': 'false'},
                            ],
                            TemporaryPassword=password
                        )

                        client.admin_add_user_to_group(
                            UserPoolId=user_pool_id,
                            Username=username,
                            GroupName=type_user
                        )

                        salt = bcrypt.gensalt()
                        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

                        insert_query = ("INSERT INTO Users (username, email, password, name, lastname, birthdate, gender, type) "
                                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
                        cursor.execute(insert_query, (username, email, hashed_password.decode('utf-8'), name, lastname, birthdate, gender, type_user))
                        connection.commit()
                        return {
                            "statusCode": 200,
                            "headers": cors_headers,
                            "body": json.dumps({
                                "message": "User inserted successfully, verification email sent"
                            }),
                        }
                    except ClientError as e:
                        logging.error('Error AWS ClientError : %s ', e)
                        raise e
                    except Exception as e:
                        logging.error('Error : %s', e)
                        raise e
                else:
                    return {
                        "statusCode": 409,
                        "headers": cors_headers,
                        "body": json.dumps({
                            "error": "Conflict - User with given username already exists"
                        }),
                    }

            else:
                return {
                    "statusCode": 409,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "error": "Conflict - User with given email already exists"
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


def generate_temporary_password(length=12):
    special_characters = '^$*.[]{}()?-"!@#%&,><:;|_~`+= '
    characters = string.ascii_letters + string.digits + special_characters

    while True:
        password = ''.join(random.choice(characters) for _ in range(length))

        has_digit = any(char.isdigit() for char in password)
        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_special = any(char in special_characters for char in password)

        if has_digit and has_upper and has_lower and has_special and len(password) >= 8:
            return password
