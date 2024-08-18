import json
import logging
import pymysql
from botocore.exceptions import ClientError
from shared.database_manager import DatabaseConfig

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,PATCH',
}

def lambda_handler(event, context):
    if event['httpMethod'] == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({
                "message": "CORS Preflight Response OK"
            })
        }

    error_message = 'Error : %s'
    error_500 = {
        "statusCode": 500,
        "headers": cors_headers,
        "body": json.dumps({
            "error": "Internal Error - Payment Method Status Not Toggled"
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

        id_paymentMethod = event['pathParameters'].get('id')

        if id_paymentMethod is None:
            raise ValueError("Bad request - Parameters are missing")

        if not id_paymentMethod.isdigit():
            raise ValueError("Bad request - Invalid request format")

        return toggle_paymentMethod_active(id_paymentMethod)

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


def toggle_paymentMethod_active(id_paymentMethod):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            search_query = "SELECT * FROM Payment_Methods WHERE id = %s"
            cursor.execute(search_query, id_paymentMethod)
            result = cursor.fetchall()

            if len(result) > 0:

                payment_method = result[0]

                payment_method_active_status = payment_method['active']
                query_active_status = 1 if payment_method_active_status == 0 else 0
                message = 'activated' if query_active_status == 1 else 'deactivated'
                toggle_query = "UPDATE Payment_Methods SET active = %s WHERE id = %s"
                cursor.execute(toggle_query, (query_active_status, id_paymentMethod))
                connection.commit()
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": f"Payment Method {message} successfully"
                    }),
                }
            else:
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "Payment Method not found"
                    }),
                }
    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e
    finally:
        connection.close()
