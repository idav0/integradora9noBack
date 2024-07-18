import json
import logging
import pymysql
from botocore.exceptions import ClientError
from datetime import date, datetime
from shared.database_manager import DatabaseConfig


def lambda_handler(event, context):
    error_message = 'Error : %s'
    error_500 = {
        "statusCode": 500,
        "body": json.dumps({
            "error": "Internal Error - User Not Found"
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

        id_user = event['pathParameters'].get('id')
        if id_user is None:
            raise ValueError("Bad request - Parameters are missing")

        if not id_user.isdigit():
            raise ValueError("Bad request - Invalid request format")

        return get_user_by_id(id_user)

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


def get_user_by_id(id_user):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            get_query = "SELECT * FROM Users Where id = %s"
            cursor.execute(get_query, id_user)
            users = cursor.fetchall()

            if len(users) > 0:
                user = users[0]
                for key, value in user.items():
                    if isinstance(value, (date, datetime)):
                        user[key] = value.isoformat()
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "user": users
                    }),
                }
            else:
                return {
                    "statusCode": 404,
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
