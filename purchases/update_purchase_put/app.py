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
    id = jsonBody['id']
    totalPrice = jsonBody['totalPrice']
    dateTime = jsonBody['dateTime']
    Users_id = jsonBody['Users_id']
    Payment_Methods_id = jsonBody['Payment_Methods_id']
    Addresses_id = jsonBody['Addresses_id']

    if not id or not totalPrice or not dateTime or not Users_id or not Payment_Methods_id or not Addresses_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing required fields"
            }),
        }

    update_purchase_put(totalPrice, dateTime, Users_id, Payment_Methods_id, Addresses_id, id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Purchase updated successfully"
        }),
    }


def update_purchase_put(totalPrice, dateTime, Users_id, Payment_Methods_id, Addresses_id, id):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            update_query = "UPDATE Purchases SET totalPrice = %s, dateTime = %s, Users_id = %s, Payment_Methods_id = %s, Adresses_id = %s  WHERE id = %s"
            cursor.execute(update_query, (totalPrice, dateTime, Users_id, Payment_Methods_id, Addresses_id, id))
            connection.commit()
    finally:
        connection.close()


