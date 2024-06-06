import json
import pymysql
import os
# import requests


MYSQL_HOST = os.getenv('RDS_HOST')
MYSQL_USER = os.getenv('RDS_USER')
MYSQL_PASSWORD = os.getenv('RDS_PASSWORD')
MYSQL_DB = os.getenv('RDS_DB')



def lambda_handler(event, context):
    jsonBody = json.loads(event['body'])
    totalPrice = jsonBody['totalPrice']
    dateTime = jsonBody['dateTime']
    Users_id = jsonBody['Users_id']
    Payment_Methods_id = jsonBody['Payment_Methods_id']
    Addresses_id = jsonBody['Addresses_id']

    if not totalPrice or not dateTime or not Users_id or not Payment_Methods_id or not Addresses_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing required fields"
            }),
        }

    insert_purchase(totalPrice, dateTime, Users_id, Payment_Methods_id, Addresses_id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Purchase inserted successfully"
        }),
    }


def insert_purchase(totalPrice, dateTime, Users_id, Payment_Methods_id, Addresses_id):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO Purchases (totalPrice, dateTime, Users_id, Payment_Methods_id, Adresses_id ) VALUES ( %s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (totalPrice, dateTime, Users_id, Payment_Methods_id, Addresses_id))
            connection.commit()
    finally:
        connection.close()

