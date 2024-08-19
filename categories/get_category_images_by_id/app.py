import json
import logging
import pymysql
from botocore.exceptions import ClientError
from shared.database_manager import DatabaseConfig

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,GET',
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
            "error": "Internal Error - Images For Category Not Found"
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

        id_category = event['pathParameters'].get('id')

        if id_category is None:
            raise ValueError("Bad request - Parameters are missing")

        if not id_category.isdigit():
            raise ValueError("Bad request - Invalid request format")

        return get_category_by_id(id_category)

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


def get_category_by_id(id_category):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:

            search_query = "SELECT * FROM Categories WHERE id = %s"
            cursor.execute(search_query, id_category)
            result = cursor.fetchall()

            if len(result) > 0:

                get_query = ("SELECT ci.url FROM Categories c JOIN Category_Images ci "
                             "ON c.id = ci.Categories_id WHERE c.id = %s")
                cursor.execute(get_query, id_category)
                category = cursor.fetchall()

                if len(category) > 0:
                    return {
                        "statusCode": 200,
                        "headers": cors_headers,
                        "body": json.dumps({
                            "category": category
                        }),
                    }
                else:
                    return {
                        "statusCode": 404,
                        "headers": cors_headers,
                        "body": json.dumps({
                            "message": "Images for Category not found"
                        }),
                    }
            else:
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "Category not found"
                    }),
                }

    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e

    finally:
        connection.close()
