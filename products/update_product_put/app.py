import json
from shared.database_manager import DatabaseConfig


def lambda_handler(event, context):

    user = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    if user.get('cognito:groups') is None or 'admin' not in user.get('cognito:groups'):
        return {
            "statusCode": 403,
            "body": json.dumps({
                "message": "Forbidden"
            }),
        }

    jsonBody = json.loads(event['body'])
    id = jsonBody['id']
    name = jsonBody['name']
    description = jsonBody['description']
    price = jsonBody['price']
    stock = jsonBody['stock']
    image = jsonBody['image']

    if id is None or name is None or description is None or price is None or stock is None or image is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing required fields"
            }),
        }

    response = update_product_put(id, name,  description, price, stock, image)
    return response





def update_product_put(id, name, description, price, stock, image):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = "UPDATE Products SET name = %s, description = %s, price = %s, stock = %s, image = %s  WHERE id = %s"
            cursor.execute(insert_query, (name, description, price, stock, image, id))
            connection.commit()
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Product updated successfully"
                }),
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal Error - Product not updated"
            }),
        }
    finally:
        connection.close()


