from login import app
import unittest
import json

mock_body = {
    "body": json.dumps({
        "username": "20193tn142@utez.edu.mx",
        "password": "Pass12&."
    })
}


class TestApp(unittest.TestCase):
    def test_lambda_handler(self):
        result = app.lambda_handler(mock_body, None)
        print(result)