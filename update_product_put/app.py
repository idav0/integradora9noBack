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
    description = jsonBody['description']
    price = jsonBody['price']
    stock = jsonBody['stock']
    image = jsonBody['image']

    if id is None or name is None or description is None or price is None or stock is None or image is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Missing required fields"
            }),
        }

    update_product_put(id, name,  description, price, stock, image)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Product updated successfully"
        }),
    }


def update_product_put(id, name, description, price, stock, image):
    connection = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            insert_query = "UPDATE Products SET name = %s, description = %s, price = %s, stock = %s, image = %s  WHERE id = %s"
            cursor.execute(insert_query, (name, description, price, stock, image, id))
            connection.commit()
    finally:
        connection.close()


