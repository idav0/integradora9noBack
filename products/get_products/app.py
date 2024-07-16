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
            "error": "Internal Error - Products Not Found"
        })
    }
    cognito_groups = ['admin', 'user']

    try:

        user = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        if user.get('cognito:groups') is None or not any(
                group in cognito_groups for group in user.get('cognito:groups')):
            return {
                "statusCode": 403,
                "body": json.dumps({
                    "message": "Forbidden"
                }),
            }

        products = get_products()
        return products

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


def get_products():
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            get_query = "SELECT * FROM Products"
            cursor.execute(get_query)
            products = cursor.fetchall()

            if len(products) > 0:
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "product": products
                    }),
                }
            else:
                return {
                    "statusCode": 404,
                    "body": json.dumps({
                        "message": "Products not found"
                    }),
                }
    except Exception as e:
        logging.error('Error : %s', e)
        raise e

    finally:
        connection.close()
