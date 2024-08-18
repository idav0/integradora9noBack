import json
import logging
import pymysql
from botocore.exceptions import ClientError
from shared.database_manager import DatabaseConfig

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,PUT',
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
            "error": "Internal Error - Address Not Updated"
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
        id_address = json_body['id']
        name = json_body['name']
        country = json_body['country']
        state = json_body['state']
        city = json_body['city']
        street = json_body['street']
        postal_code = json_body['postal_code']
        Users_id = json_body['Users_id']

        if not all([id_address, name, country, state, city, street, postal_code, Users_id]):
            raise ValueError("Bad request - Parameters are missing")

        return update_address(id_address, name, country, state, city, street, postal_code, Users_id)

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

def update_address(id_address, name, country, state, city, street, postal_code, Users_id):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            search_query = "SELECT * FROM Addresses WHERE id = %s"
            cursor.execute(search_query, id_address)
            result = cursor.fetchall()

            if len(result) > 0:
                update_query = ("UPDATE Addresses SET name = %s, country = %s, state = %s, city = %s, street = %s, "
                                "postal_code = %s, Users_id = %s WHERE id = %s")
                cursor.execute(update_query, (name, country, state, city, street, postal_code, Users_id, id_address))
                connection.commit()
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "Address updated successfully"
                    }),
                }
            else:
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "Address not found"
                    }),
                }
    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e
    finally:
        connection.close()
