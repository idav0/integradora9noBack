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

    def test_bcrypt_encrpyt(self):

        passw = 'Pass12&.'

        # Hashing the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(passw.encode('utf-8'), salt)
        print(hashed)

        hashed_decode = hashed.decode('utf-8')
        print(hashed_decode)


    def test_bcrypt_decrypt(self):

        passw = 'ContraPrueba123.'

        hashed_decode = '$2b$12$AJuRDjEnUwbg8lluH29i4ub/5otbFC.UDaBK9hn/ZI29Ov6RJYrEW'

        confirm_old_password = bcrypt.checkpw(passw.encode('utf-8'), hashed_decode.encode('utf-8'))
        print(confirm_old_password)


