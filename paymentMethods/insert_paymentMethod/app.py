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
    name = jsonBody['name']
    info = jsonBody['info']
    Users_id = jsonBody['Users_id']

    if not name or not info or not Users_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing required fields"
            }),
        }

    insert_paymentMethod(name, info, Users_id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Payment Method inserted successfully"
        }),
    }


def insert_paymentMethod(name, info, Users_id):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO Payment_Methods (name, info, Users_id) VALUES ( %s, %s, %s)"
            cursor.execute(insert_query, (name, info, Users_id))
            connection.commit()
    finally:
        connection.close()

