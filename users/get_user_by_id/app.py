import json
from datetime import date, datetime
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

    id = event['pathParameters'].get('id')
    user = get_user_by_id(id)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "user": user
        }),
    }


def get_user_by_id(id):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    users = []

    try:
        with connection.cursor() as cursor:
            get_query = "SELECT * FROM Users Where id = %s"
            cursor.execute(get_query, id)
            users = cursor.fetchall()
    finally:
        connection.close()

    # Convert any date or datetime objects to strings
    for user in users:
        for key, value in user.items():
            if isinstance(value, (date, datetime)):
                user[key] = value.isoformat()

    return users
