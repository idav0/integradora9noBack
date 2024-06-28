import json
import logging
from shared.database_manager import DatabaseConfig


def lambda_handler(event, ):
    body_id = event['pathParameters'].get('id')

    if body_id is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "The id is required"
            }),
        }

    address = get_address_by_id(body_id)

    if address is None:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "message": "Address not found"
            }),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "address": address
        }),
    }


def get_address_by_id(body_id):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            get_query = "SELECT * FROM Addresses WHERE id = %s"
            cursor.execute(get_query, body_id)
            addresses = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal Error - Address not found"
            }),
        }
    finally:
        connection.close()
        return addresses
