import unittest
import json
import bcrypt


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

    def test_bcrypt(self):

        passw = 'ContraPrueba123.'
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(passw.encode('utf-8'), salt)
        print(hashed)
        hashed_decode = hashed.decode('utf-8')
        print(hashed_decode)

        confirm_old_password = bcrypt.checkpw(passw.encode('utf-8'), hashed_decode.encode('utf-8'))
        print(confirm_old_password)


