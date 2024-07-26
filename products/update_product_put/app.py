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
        id_product = json_body['id']
        name = json_body['name']
        description = json_body['description']
        price = json_body['price']
        stock = json_body['stock']
        discount = json_body['discount']
        #image = json_body['image']
        category_id = json_body['category_id']

        if id_product is None or name is None or description is None or price is None or stock is None or discount is None or category_id is None:
            raise ValueError("Bad request - Parameters are missing")

        return update_product_put(id_product, name,  description, price, stock, discount, category_id)

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


def update_product_put(id_product, name, description, price, stock, discount, category_id):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            search_query = "SELECT * FROM Products WHERE id = %s"
            cursor.execute(search_query, id_product)
            result = cursor.fetchall()

            if len(result) > 0:
                update_query = ("UPDATE Products SET name = %s, description = %s, price = %s, stock = %s, discount = %s, category_id = %s "
                                "WHERE id = %s")
                cursor.execute(update_query, (name, description, price, stock, discount, category_id, id_product))
                connection.commit()
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "message": "Product updated successfully"
                    }),
                }
            else:
                return {
                    "statusCode": 404,
                    "body": json.dumps({
                        "message": "Product not found"
                    }),
                }
    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e
    finally:
        connection.close()
