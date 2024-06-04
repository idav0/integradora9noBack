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
    email = jsonBody['email']
    password = jsonBody['password']
    name = jsonBody['name']
    lastname = jsonBody['lastname']
    birthdate = jsonBody['birthdate']
    gender = jsonBody['gender']
    type = jsonBody['type']

    if email is None or password is None or name is None or lastname is None or birthdate is None or gender is None or type is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing required fields"
            }),
        }

    insert_user(email, password, name, lastname, birthdate, gender, type)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "User inserted successfully"
        }),
    }


def insert_user(email, password, name, lastname, birthdate, gender, type):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO Users (email, password, name, lastname, birthdate, gender, type) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (email, password, name, lastname, birthdate, gender, type))
            connection.commit()
    finally:
        connection.close()


