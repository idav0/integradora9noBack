import json
import logging
import pymysql
from botocore.exceptions import ClientError
from datetime import date, datetime
from shared.database_manager import DatabaseConfig

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,GET',
}

def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({
                "message": "CORS Preflight Response  OK"
            })
        }

    error_message = 'Error : %s'
    error_500 = {
        "statusCode": 500,
        "headers": cors_headers,
        "body": json.dumps({
            "error": "Internal Error - User Not Deleted"
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

        return get_users()

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


def get_users():
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            get_query = "SELECT * FROM Users"
            cursor.execute(get_query)
            users = cursor.fetchall()

            if len(users) > 0:
                for user in users:
                    for key, value in user.items():
                        if isinstance(value, (date, datetime)):
                            user[key] = value.isoformat()
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "users": users
                    }),
                }
            else:
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "error": "Not Found - No Users Found"
                    })
                }
    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e

    finally:
        connection.close()
