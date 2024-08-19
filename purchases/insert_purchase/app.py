import json
import logging
import pymysql
from botocore.exceptions import ClientError
from collections import Counter
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
            "error": "Internal Error - Purchase Not Inserted"
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
        total_price = json_body.get('totalPrice')
        datetime_purchase = json_body.get('datetime')
        users_id = json_body.get('users_id')
        payment_method_id = json_body.get('paymentMethod_id')
        address_id = json_body.get('address_id')
        products = json_body.get('products')

        if not (total_price and datetime_purchase and users_id and payment_method_id and address_id and products):
            raise ValueError("Bad request - Parameters are missing")

        return insert_purchase(total_price, datetime_purchase, users_id, payment_method_id, address_id, products)

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

def insert_purchase(total_price, datetime_purchase, users_id, payment_method_id, address_id, products):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:

            product_counter = Counter([product['id'] for product in products])

            for product_id, quantity in product_counter.items():
                stock_query = "SELECT stock FROM Products WHERE id = %s"
                cursor.execute(stock_query, (product_id,))
                stock_result = cursor.fetchone()

                if not stock_result or stock_result['stock'] < quantity:
                    raise ValueError(f"Insufficient stock for product ID {product_id}")

            insert_purchase_query = """
                INSERT INTO Purchases (totalPrice, datetime, Users_id, Payment_Methods_id, Adresses_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_purchase_query, (total_price, datetime_purchase, users_id, payment_method_id, address_id))
            purchase_id = cursor.lastrowid

            for product_id, quantity in product_counter.items():
                insert_intermediate_query = """
                    INSERT INTO Products_has_Purchases (Products_id, Purchases_id, quantity)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_intermediate_query, (product_id, purchase_id, quantity))

                update_stock_query = "UPDATE Products SET stock = stock - %s WHERE id = %s"
                cursor.execute(update_stock_query, (quantity, product_id))

            connection.commit()
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "message": "Purchase and products inserted successfully",
                    "purchase_id": purchase_id
                }),
            }

    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e

    finally:
        connection.close()
