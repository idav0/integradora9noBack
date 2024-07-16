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
            "error": "Internal Error - Product Not Deleted"
        })
    }
    cognito_groups = ['admin']

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

        id_product = event['pathParameters'].get('id')

        if id_product is None:
            raise ValueError("Bad request - Parameters are missing")

        response = delete_user_by_id(id_product)
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


def delete_user_by_id(id_product):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            delete_query = "DELETE FROM Products WHERE id = %s"
            cursor.execute(delete_query, id_product)
            connection.commit()
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Product deleted successfully"
                }),
            }
    except Exception as e:
        logging.error('Error : %s', e)
        raise e
    finally:
        connection.close()
