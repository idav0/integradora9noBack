import json
import logging
import pymysql
from botocore.exceptions import ClientError
from shared.database_manager import DatabaseConfig


def lambda_handler(event, context):
    error_message = 'Error : %s'
    error_500 = {
        "statusCode": 500,
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
                "body": json.dumps({
                    "message": "Forbidden"
                }),
            }

        json_body = json.loads(event['body'])
        name = json_body['name']
        description = json_body['description']
        price = json_body['price']
        stock = json_body['stock']
        image = json_body['image']

        if name is None or description is None or price is None or stock is None or image is None:
            raise ValueError("Bad request - Parameters are missing")

        response = insert_product(name,  description, price, stock, image)
        return response

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


def insert_product(name,  description, price, stock, image):
    db = DatabaseConfig()
    connection = db.get_new_connection()
    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO Products ( name, description, price, stock, image) VALUES ( %s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (name,  description, price, stock, image))
            connection.commit()
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Product inserted successfully"
                }),
            }
    except Exception as e:
        logging.error('Error : %s', e)
        raise e
    finally:
        connection.close()
