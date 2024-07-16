from set_password import app
import unittest
import json


mock_body = {
    "body": json.dumps({
        "username": "20213tn079@utez.edu.mx",
        "temporary_password": "o[p9cmS FQL2",
        "new_password": "Pass34&."
    })
}


class TestApp(unittest.TestCase):
    def test_lambda_handler(self):
        result = app.lambda_handler(mock_body, None)
        print(result)