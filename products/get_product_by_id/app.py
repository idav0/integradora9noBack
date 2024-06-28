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

    id = event['pathParameters'].get('id')
    product = get_product_by_id(id)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "product": product
        }),
    }


def get_product_by_id(id):
    db = DatabaseConfig()
    connection = db.get_new_connection()
    products = []

    try:
        with connection.cursor() as cursor:
            get_query = "SELECT * FROM Products WHERE id = %s"
            cursor.execute(get_query, id)
            products = cursor.fetchall()
    finally:
        connection.close()

    return products
