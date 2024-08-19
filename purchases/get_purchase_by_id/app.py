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
            "error": "Internal Error - Purchase Not Found"
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

        id_purchase = event['pathParameters'].get('id')

        if id_purchase is None:
            raise ValueError("Bad request - Parameters are missing")

        if not id_purchase.isdigit():
            raise ValueError("Bad request - Invalid request format")

        return get_purchase_by_id(id_purchase)

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


def get_purchase_by_id(id_purchase):
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
                         "JOIN Products pr ON pp.Products_id = pr.id WHERE p.id = %s")
            cursor.execute(get_query, id_purchase)
            purchase = cursor.fetchall()

            if len(purchase) > 0:

                object_purchase = {
                    "purchase_id": purchase[0]["purchase_id"],
                    "totalPrice": purchase[0]["totalPrice"],
                    "datetime": purchase[0]["datetime"],
                    "users_id": purchase[0]["Users_id"],
                    "paymentMethod_id": purchase[0]["Payment_Methods_id"],
                    "address_id": purchase[0]["Adresses_id"],
                    "products": []
                }

                for row in purchase:
                    product = {
                        "product_id": row["product_id"],
                        "name": row["product_name"],
                        "description": row["product_description"],
                        "price": row["product_price"],
                        "discount": row["product_discount"],
                        "stock": row["product_stock"],
                        "image": row["product_image"],
                        "active": row["product_active"],
                        "quantity": row["product_quantity"]
                    }
                    object_purchase["products"].append(product)

                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "purchase": object_purchase
                    }),
                }
            else:
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "message": "Purchase not found"
                    }),
                }

    except Exception as e:
        logging.error('Error : %s', e)
        connection.rollback()
        raise e

    finally:
        connection.close()
