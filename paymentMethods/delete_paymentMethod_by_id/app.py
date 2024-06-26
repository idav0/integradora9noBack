import json
import pymysql
from datetime import date, datetime
import os
# import requests


MYSQL_HOST = os.getenv('RDS_HOST')
MYSQL_USER = os.getenv('RDS_USER')
MYSQL_PASSWORD = os.getenv('RDS_PASSWORD')
MYSQL_DB = os.getenv('RDS_DB')



def lambda_handler(event, context):
    id = event['pathParameters'].get('id')

    if id is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "The id is required"
            }),
        }

    delete_paymentMethod_by_id(id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Payment Method deleted successfully"
        }),
    }


def delete_paymentMethod_by_id(id):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            delete_query = "DELETE FROM Payment_Methods WHERE id = %s"
            cursor.execute(delete_query, id)
            connection.commit()
    finally:
        connection.close()

