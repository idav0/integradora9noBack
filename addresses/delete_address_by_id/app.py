import json
from shared.database_manager import DatabaseConfig


def lambda_handler(event,context ):
    id = event['pathParameters'].get('id')

    if id is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "The id is required"
            }),
        }

    delete_address_by_id(id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Product deleted successfully"
        }),
    }


def delete_address_by_id(id):
    db = DatabaseConfig()
    connection = db.get_new_connection()
    try:
        with connection.cursor() as cursor:
            delete_query = "DELETE FROM Addresses WHERE id = %s"
            cursor.execute(delete_query, id)
            connection.commit()
    finally:
        connection.close()
