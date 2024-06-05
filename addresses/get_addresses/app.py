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
    addresses = get_addresses()
    return {
        "statusCode": 200,
        "body": json.dumps({
            "addresses": addresses
        }),
    }


def get_addresses():
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)
    addresses = []

    try:
        with connection.cursor() as cursor:
            get_query = "SELECT * FROM Addresses"
            cursor.execute(get_query)
            addresses = cursor.fetchall()
    finally:
        connection.close()

    return addresses
