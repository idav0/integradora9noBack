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
            "error": "Internal Error - User Not Updated"
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
        email = json_body['email']
        password = json_body['password']
        name = json_body['name']
        lastname = json_body['lastname']
        birthdate = json_body['birthdate']
        gender = json_body['gender']
        type_user = json_body['type']
        id_user = json_body['id']

        if (email is None or password is None or name is None or lastname is None or birthdate is None or gender is None
                or type_user is None or id_user is None):
            raise ValueError("Bad request - Parameters are missing")

        return update_user_put(email, password, name, lastname, birthdate, gender, type_user, id_user)

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


def update_user_put(email, password, name, lastname, birthdate, gender, type_user, id_user):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            search_query = "SELECT * FROM Users WHERE id = %s"
            cursor.execute(search_query, id_user)
            result = cursor.fetchall()

            if len(result) > 0:
                insert_query = ("UPDATE Users SET email=%s, password=%s, name=%s, lastname=%s, birthdate=%s, "
                                "gender = %s, type = %s WHERE id = %s")
                cursor.execute(insert_query, (email, password, name, lastname, birthdate, gender, type_user, id_user))
                connection.commit()
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "message": "User Updated Successfully"
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
