import json
from shared.database_manager import DatabaseConfig


def lambda_handler(event, context):
    user = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    if user.get('cognito:groups') is None or ('admin' not in user.get('cognito:groups') and 'user' not in user.get('cognito:groups')):
        return {
            "statusCode": 403,
            "body": json.dumps({
                "message": "Forbidden"
            }),
        }

    products = get_products()
    return {
        "statusCode": 200,
        "body": json.dumps({
            "products": products
        }),
    }


def get_products():
    db = DatabaseConfig()
    connection = db.get_new_connection()
    products = []

    try:
        with connection.cursor() as cursor:
            get_query = "SELECT * FROM Products"
            cursor.execute(get_query)
            products = cursor.fetchall()
    finally:
        connection.close()

    return products
