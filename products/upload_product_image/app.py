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
    error_message = 'Error : %s'
    error_500 = {
        "statusCode": 500,
        "body": json.dumps({
            "error": "Internal Error - Image Not Uploaded"
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
                "body": json.dumps({
                    "message": "Forbidden"
                }),
            }

        json_body = json.loads(event['body'])
        image_data = json_body['image_data']
        image_name_id = json_body['image_name_id']
        image_type = json_body['image_type']

        if image_name_id is None or image_data is None or image_type is None:
            raise ValueError("Bad request - Parameters are missing")

        db = DatabaseConfig()
        connection = db.get_connection()

        try:
            image_data = base64.b64decode(image_data)

            with connection.cursor() as cursor:
                search_product_query = "SELECT * FROM Products WHERE id = %s"
                cursor.execute(search_product_query, image_name_id)
                product = cursor.fetchall()

                if len(product) > 0:

                    object_key = "products/" + image_name_id + "." + image_type

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

                    upload_image_query = "UPDATE Products SET image = %s WHERE id = %s"
                    cursor.execute(upload_image_query, (object_url, image_name_id))
                    connection.commit()

                    return {
                        "statusCode": 200,
                        "body": json.dumps({
                            "image_url": object_url
                        })
                    }

                else:
                    return {
                        "statusCode": 404,
                        "body": json.dumps({
                            "error": "Product not found, image not uploaded"
                        })
                    }
        except pymysql.MySQLError as e:
            logging.error('Error MySQL : %s', e)
            raise e
        except ClientError as e:
            logging.error('Error AWS ClientError : %s', e)
            raise e
        finally:
            connection.close()


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


def get_secret(secret_name: str, region_name: str) -> Dict[str, str]:
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logging.error("Failed to retrieve secret: %s", e)
        raise e

    return json.loads(get_secret_value_response['SecretString'])
