import unittest
from unittest import TestCase
from unittest.mock import patch

from addresses.insert_address import app

import json

mock_body = {
    "body": json.dumps({
        "name": "nombreUnitTest",
        "country": "paisTest",
        "state": "estadoTest",
        "city": "ciudadTest",
        "street": "calleTest",
        "postal_code": 60100,
        "Users_id": 1
    })
}

mock_pathParameters = {
    "pathParameters": {
        "name": "nombreUnitTest"
    }
}



class TestInsertAddress(unittest.TestCase):

    #@patch.dic("os.getenv", {"RDS_HOST":"database-mysql-10.cniakw00enzf.us-east-1.rds.amazonaws.com", "RDS_USER": "admin", "RDS_PASSWORD": "admin123", "RDS_DB": "integradorashopeasy"})
    @patch.dic("os.getenv", {"RDS_HOST":"host", "RDS_USER": "user", "RDS_PASSWORD": "password", "RDS_DB": "basededatos"})
    @patch("connection")
    def test_lambda_handler(self):
        result = app.lambda_handler(mock_body, None)
        self.assertEqual(result["statusCode"],200)
        body = json.loads(result["body"])
        self.assertIs("data", body)
        self.assertTrue(body["data"])
