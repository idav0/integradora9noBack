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
            "error": "Internal Error - Product Not Updated"
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

        json_body = json.loads(event['body'])
        id_product = json_body['id']
        name = json_body['name']
        description = json_body['description']
        price = json_body['price']
        stock = json_body['stock']
        image = json_body['image']

        if id_product is None or name is None or description is None or price is None or stock is None or image is None:
            raise ValueError("Bad request - Parameters are missing")

        response = update_product_put(id_product, name,  description, price, stock, image)
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


def update_product_put(id_product, name, description, price, stock, image):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = ("UPDATE Products SET name = %s, description = %s, price = %s, stock = %s, image = %s  "
                            "WHERE id = %s")
            cursor.execute(insert_query, (name, description, price, stock, image, id_product))
            connection.commit()
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Product updated successfully"
                }),
            }
    except Exception as e:
        logging.error('Error : %s', e)
        raise e
    finally:
        connection.close()
