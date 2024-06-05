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
    name = jsonBody['name']
    info = jsonBody['info']
    Users_id = jsonBody['Users_id']

    if not id or not name or not info or not Users_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing required fields"
            }),
        }

    update_paymentMethod_put(id, name, info, Users_id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "PaymentMethod updated successfully"
        }),
    }


def update_paymentMethod_put(id, name, info, Users_id):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            update_query = "UPDATE Payment_Methods SET name = %s, info = %s, Users_id = %s  WHERE id = %s"
            cursor.execute(update_query, (name, info, Users_id, id))
            connection.commit()
    finally:
        connection.close()


