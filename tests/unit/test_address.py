f
from addresses.delete_address_by_id.app import lambda_handler
import json


class Test(unittest.TestCase):

    @patch('addresses.delete_address_by_id.app.delete_address_by_id')
    def test_lambda_handler(self, mock_delete_address_by_id):

        mock_delete_address_by_id.side_effect = Exception('error')

        response = lambda_handler({'pathParameters': {'id': '1'}},)

        self.assertEqual(response['statusCode'], 500)
