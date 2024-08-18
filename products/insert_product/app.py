import json
import logging
import pymysql
import base64
import boto3
from typing import Dict
import os
from botocore.exceptions import ClientError
from shared.database_manager import DatabaseConfig

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST',
}


def lambda_handler(event, context):
    if event['httpMethod'] == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({
                "message": "CORS preflight response OK"
            })
        }

    error_message = 'Error : %s'
    error_500 = {
        "statusCode": 500,
        "headers": cors_headers,
        "body": json.dumps({
            "error": "Internal Error - Product Not Inserted"
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
        name = json_body['name']
        description = json_body['description']
        price = json_body['price']
        stock = json_body['stock']
        discount = json_body['discount']
        image_data = json_body['image_data']
        image_type = json_body['image_type']
        category_id = json_body['category_id']

        if (name is None or description is None or price is None or stock is None
                or discount is None or category_id is None):
            raise ValueError("Bad request - Parameters are missing")

        return insert_product(name, description, price, stock, discount, image_data, image_type, category_id)

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


def insert_product(name,  description, price, stock, discount, image_data, image_type, category_id):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        if image_data != "" and image_type != "":
            with connection.cursor() as cursor:
                search_query = "SELECT * FROM Products ORDER BY id DESC LIMIT 1"
                cursor.execute(search_query)
                result = cursor.fetchall()

                if len(result) > 0:
                    last_id = result[0]['id']
                else:
                    last_id = 0

                image_data = base64.b64decode(image_data)
                object_key = "products/" + str(last_id + 1) + "." + image_type

                region_name = os.environ.get('REGION_NAME')
                secret_name = os.environ.get('SECRET_NAME')

                if region_name is None or secret_name is None:
                    raise ValueError("Internal Error - Parameters are missing")

                secrets = get_secret(secret_name, region_name)

                if secrets is None or secrets['BUCKET_NAME'] is None:
                    raise ValueError("Internal Error - Parameters are missing")

                bucket_name = secrets['BUCKET_NAME']

                s3 = boto3.client('s3')
                s3.put_object(Bucket=bucket_name, Key=object_key, Body=image_data)

                object_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{object_key}"

                insert_query = ("INSERT INTO Products (name, description, price, stock, discount, image, Category_id) "
                                "VALUES ( %s, %s, %s, %s, %s, %s, %s)")
                cursor.execute(insert_query, (name,  description, price, stock, discount, object_url, category_id))
                connection.commit()
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "Product inserted successfully with image",
                    }),
                }
        else:
            with connection.cursor() as cursor:
                insert_query = ("INSERT INTO Products (name, description, price, stock, discount, Category_id) "
                                "VALUES ( %s, %s, %s, %s, %s, %s)")
                cursor.execute(insert_query, (name,  description, price, stock, discount, category_id))
                connection.commit()
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "Product inserted successfully without image",
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
