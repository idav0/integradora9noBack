import json
import logging
import os
import random
import string
import pymysql
import boto3
from typing import Dict
from botocore.exceptions import ClientError
from shared.database_manager import DatabaseConfig


def lambda_handler(event, context):
    error_message = 'Error : %s'
    error_500 = {
        "statusCode": 500,
        "body": json.dumps({
            "error": "Internal Error - User Not Inserted"
        })
    }

    try:

        json_body = json.loads(event['body'])
        email = json_body['email']
        password = generate_temporary_password()
        name = json_body['name']
        lastname = json_body['lastname']
        birthdate = json_body['birthdate']
        gender = json_body['gender']
        type_user = json_body['type']

        if (email is None or password is None or name is None or lastname is None or birthdate is None or gender is None
                or type_user is None):
            raise ValueError("Bad request - Parameters are missing")

        return insert_user(email, password, name, lastname, birthdate, gender, type_user)

    except KeyError as e:
        logging.error(error_message, e)
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Bad request - Invalid request format"
            })
        }

    except ValueError as e:
        logging.error(error_message, e)
        return {
            "statusCode": 400,
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


def insert_user(email, password, name, lastname, birthdate, gender, type_user):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            search_query = "SELECT * FROM Users WHERE email = %s"
            cursor.execute(search_query, email)
            result = cursor.fetchall()

            if len(result) == 0:
                try:
                    secret_name = os.getenv("SECRET_NAME")
                    region_name = os.getenv("REGION_NAME")
                    print(secret_name, region_name)
                    secrets = get_secret(secret_name, region_name)
                    print(secrets)
                    print(secrets)
                    client = boto3.client('cognito-idp', region_name=region_name)
                    print(client)
                    user_pool_id = secrets['USER_POOL_ID']
                    role = 'user'

                    client.admin_create_user(
                        UserPoolId=user_pool_id,
                        Username=email,
                        UserAttributes=[
                            {'Name': 'email', 'Value': email},
                            {'Name': 'email_verified', 'Value': 'false'},
                        ],
                        TemporaryPassword=password
                    )

                    client.admin_add_user_to_group(
                        UserPoolId=user_pool_id,
                        Username=email,
                        GroupName=role
                    )

                    insert_query = ("INSERT INTO Users (email, password, name, lastname, birthdate, gender, type) "
                                    "VALUES (%s, %s, %s, %s, %s, %s, %s)")
                    cursor.execute(insert_query, (email, password, name, lastname, birthdate, gender, type_user))
                    connection.commit()
                    return {
                        "statusCode": 200,
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
    special_characters = '^$*.[]{}()?-"!@#%&/\\,><\':;|_~`+= '
    characters = string.ascii_letters + string.digits + special_characters

    while True:
        password = ''.join(random.choice(characters) for _ in range(length))

        has_digit = any(char.isdigit() for char in password)
        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_special = any(char in special_characters for char in password)

        if has_digit and has_upper and has_lower and has_special and len(password) >= 8:
            return password
