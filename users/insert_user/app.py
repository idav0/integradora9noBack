import json
from shared.database_manager import DatabaseConfig



def lambda_handler(event, context):
    user = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    if user.get('cognito:groups') is None or 'admin' not in user.get('cognito:groups'):
        return {
            "statusCode": 403,
            "body": json.dumps({
                "message": "Forbidden"
            }),
        }

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



def insert_user(email, password, name, lastname, birthdate, gender, type):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO Users (email, password, name, lastname, birthdate, gender, type) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (email, password, name, lastname, birthdate, gender, type))
            connection.commit()
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "User inserted successfully"
                }),
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal Error - User not inserted"
            }),
        }

    finally:
        connection.close()


