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

    id = event['pathParameters'].get('id')

    if id is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "id is required"
            }),
        }

    delete_user_by_id(id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "User deleted successfully"
        }),
    }




def delete_user_by_id(id):
    db = DatabaseConfig()
    connection = db.get_new_connection()

    try:
        with connection.cursor() as cursor:
            delete_query = "DELETE FROM Users WHERE id = %s"
            cursor.execute(delete_query, id)
            connection.commit()
    finally:
        connection.close()

