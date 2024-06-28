import json
import logging

import pymysql

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

    try:
        delete_address_by_id(body_id)
    except Exception as e:
        logging.error(f"Error deleting address with id {body_id}: {e} ")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal Error - Address not deleted "
            }),
        }


def delete_address_by_id(body_id):
    db = DatabaseConfig()

    connection = db.get_new_connection()

    if not connection:
        raise ValueError("Failed to connect to database")

    try:
        with connection.cursor() as cursor:
            delete_query = "DELETE FROM Addresses WHERE id = %s"
            cursor.execute(delete_query, (body_id,))
            connection.commit()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Address deleted successfully"
            }),
        }
    except pymysql.Error as e:
        logging.error(f"Error executing delete query: {e}")
        raise
    finally:
        if connection:
            connection.close()
