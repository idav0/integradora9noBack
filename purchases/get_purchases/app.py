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
            "error": "Internal Error - Purchases Not Found"
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

        return get_purchases()

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


def get_purchases():
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            get_query = ("SELECT p.id "
                         "AS purchase_id, p.totalPrice, p.datetime, p.Users_id, p.Payment_Methods_id, p.Adresses_id, pr.id "
                         "AS product_id, pr.name AS product_name, pr.description AS product_description, pr.price "
                         "AS product_price, pr.discount AS product_discount, pr.stock AS product_stock, pr.image "
                         "AS product_image, pr.active AS product_active, pp.quantity AS product_quantity "
                         "FROM Purchases p JOIN Products_has_Purchases pp ON p.id = pp.Purchases_id "
                         "JOIN Products pr ON pp.Products_id = pr.id")
            cursor.execute(get_query)
            rows = cursor.fetchall()

            if len(rows) > 0:

                purchases = {}
                for row in rows:
                    purchase_id = row['purchase_id']
                    if purchase_id not in purchases:
                        purchases[purchase_id] = {
                            "purchase_id": purchase_id,
                            "totalPrice": row['totalPrice'],
                            "datetime": row['datetime'].isoformat(),
                            "users_id": row['Users_id'],
                            "paymentMethod_id": row['Payment_Methods_id'],
                            "address_id": row['Adresses_id'],
                            "products": []
                        }

                    product = {
                        "product_id": row['product_id'],
                        "name": row['product_name'],
                        "description": row['product_description'],
                        "price": row['product_price'],
                        "discount": row['product_discount'],
                        "stock": row['product_stock'],
                        "image": row['product_image'],
                        "active": row['product_active'],
                        "quantity": row['product_quantity']
                    }

                    purchases[purchase_id]["products"].append(product)

                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "purchases": purchases
                    }),
                }
            else:
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "Purchases not found"
                    }),
                }

    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e

    finally:
        connection.close()
