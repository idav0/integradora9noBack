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
    country = jsonBody['country']
    state = jsonBody['state']
    city = jsonBody['city']
    street = jsonBody['street']
    postal_code = jsonBody['postal_code']
    Users_id = jsonBody['Users_id']

    if not id or not name or not country or not state or not city or not street or not postal_code or not Users_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing required fields"
            }),
        }

    update_address_put(id, name, country, state, city, street, postal_code, Users_id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Address updated successfully"
        }),
    }


def update_address_put(id, name, country, state, city, street, postal_code, Users_id):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            update_query = "UPDATE Addresses SET name = %s, country = %s, state = %s, city = %s, street = %s, postal_code = %s, Users_id = %s WHERE id = %s"
            cursor.execute(update_query, (name, country, state, city, street, postal_code, Users_id, id))
            connection.commit()
    finally:
        connection.close()


