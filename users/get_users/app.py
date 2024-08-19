import json
import logging
import pymysql
from botocore.exceptions import ClientError
from datetime import date, datetime
from shared.database_manager import DatabaseConfig

logging.basicConfig(level=logging.INFO)

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,GET',
}

def lambda_handler(event, context):
    logging.info("Lambda function started")

    if event.get('httpMethod') == 'OPTIONS':
        logging.info("CORS Preflight request")
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
        logging.info("Extracting user info from requestContext")
        user = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        logging.info(f"User claims: {user}")

        user_cognito_groups = user.get(cognito_groups, '').split(',') if isinstance(user.get(cognito_groups), str) \
            else user.get(cognito_groups, [])
        logging.info(f"User groups: {user_cognito_groups}")

        if user.get(cognito_groups) is None or not any(
                group in required_cognito_groups for group in user_cognito_groups):
            logging.warning("Forbidden access - User is not in required groups")
            return {
                "statusCode": 403,
                "headers": cors_headers,
                "body": json.dumps({
                    "message": "Forbidden"
                }),
            }

        logging.info("Calling get_users()")
        return get_users()

    except KeyError as e:
        logging.error("KeyError: %s", e)
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps({
                "error": "Bad request - Invalid request format"
            })
        }

    except ValueError as e:
        logging.error("ValueError: %s", e)
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps({
                "error": str(e)
            })
        }

    except ClientError as e:
        logging.error("ClientError: %s", e)
        return error_500

    except pymysql.MySQLError as e:
        logging.error("MySQLError: %s", e)
        return error_500

    except Exception as e:
        logging.error("General Exception: %s", e)
        return error_500


def get_users():
    logging.info("Entered get_users function")
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            logging.info("Executing SQL query to get users")
            get_query = "SELECT * FROM Users"
            cursor.execute(get_query)
            users = cursor.fetchall()

            if len(users) > 0:
                logging.info("Users found, processing results")
                for user in users:
                    for key, value in user.items():
                        if isinstance(value, (date, datetime)):
                            user[key] = value.isoformat()
                logging.info("Returning list of users")
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "users": users
                }
            else:
                logging.warning("No users found")
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "error": "Not Found - No Users Found"
                    })
                }
    except Exception as e:
        logging.error('Error in get_users: %s', e)
        connection.rollback()
        raise e

    finally:
        logging.info("Closing database connection")
        connection.close()
