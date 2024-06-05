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
    paymentMethods = get_paymentMethod_by_id(id)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "paymentMethod": paymentMethods
        }),
    }


def get_paymentMethod_by_id(id):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)
    paymentMethods = []

    try:
        with connection.cursor() as cursor:
            get_query = "SELECT * FROM Payment_Methods WHERE id = %s"
            cursor.execute(get_query, id)
            paymentMethods = cursor.fetchall()
    finally:
        connection.close()

    return paymentMethods
