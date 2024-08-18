import json
import logging
import pymysql
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
            "error": "Internal Error - Payment Method Not Inserted"
        })
    }
    required_cognito_groups = ['admin', 'user']
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
        alias = json_body['alias']
        card_owner = json_body['card_owner']
        card_number = json_body['card_number']
        card_expiration = json_body['card_expiration']
        card_cvv = json_body['card_cvv']
        card_type = json_body['card_type']
        card_zip = json_body['card_zip']
        Users_id = json_body['Users_id']

        if not all([alias, card_owner, card_number, card_expiration, card_cvv, card_type, card_zip, Users_id]):
            raise ValueError("Bad request - Parameters are missing")

        return insert_paymentMethod(alias, card_owner, card_number, card_expiration, card_cvv, card_type, card_zip, Users_id)

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


def insert_paymentMethod(alias, card_owner, card_number, card_expiration, card_cvv, card_type, card_zip, Users_id):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:

            search_query = ("SELECT * FROM Users WHERE id = %s")
            cursor.execute(search_query, Users_id)
            result = cursor.fetchall()

            if result > 0:

                insert_query = ("INSERT INTO Payment_Methods (alias, card_owner, card_number, card_expiration, card_cvv, "
                                "card_type, card_zip, Users_id)"
                                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
                cursor.execute(insert_query, (alias, card_owner, card_number, card_expiration, card_cvv, card_type, card_zip, Users_id))
                connection.commit()
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "Payment Method inserted successfully"
                    }),
                }
            else:
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "User not found"
                    }),
                }

    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e

    finally:
        connection.close()
