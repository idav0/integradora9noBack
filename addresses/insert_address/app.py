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
    country = jsonBody['country']
    state = jsonBody['state']
    city = jsonBody['city']
    street = jsonBody['street']
    postal_code = jsonBody['postal_code']
    Users_id = jsonBody['Users_id']

    if not name or not country or not state or not city or not street or not postal_code or not Users_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing required fields"
            }),
        }

    insert_address(name, country, state, city, street, postal_code, Users_id)




def insert_address(name, country, state, city, street, postal_code, Users_id):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO Addresses (name, country, state, city, postal_code, Users_id) VALUES ( %s, %s)"
            cursor.execute(insert_query, (name, country, state, city, street, postal_code, Users_id))
            connection.commit()
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Address inserted successfully"
                }),
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal Error - Address not inserted"
            }),
        }

    finally:
        connection.close()

