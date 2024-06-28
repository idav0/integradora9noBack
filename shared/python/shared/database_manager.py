import os
import pymysql
import logging
import boto3
import json
from typing import Dict

from botocore.exceptions import ClientError


class DatabaseConfig:
    def __init__(self):

        try:
            self.__secret_name = os.getenv("RDS_SECRET_NAME")
            self.__region_name = os.getenv("RDS_REGION")
            self.__secret = self.__get_secret(self.__secret_name, self.__region_name)
        except ClientError as e:
            print(e)

        self.__mysql_host = self.__secret["RDS_HOST"]
        self.__mysql_db = self.__secret["RDS_DB"]
        self.__mysql_user = self.__secret["RDS_USER"]
        self.__mysql_password = self.__secret["RDS_PASSWORD"]

    def __create_connection(self):
        print(self.__mysql_host)
        print(self.__mysql_db)
        print(self.__mysql_user)
        print(self.__mysql_password)
        try:
            connection = pymysql.connect(
                host=self.__mysql_host,
                database=self.__mysql_db,
                user=self.__mysql_user,
                password=self.__mysql_password,
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except pymysql.MySQLError as error:
            logging.error(error)
            return None

    def get_new_connection(self):
        return self.__create_connection()

    def __get_secret(secret_name: str, region_name: str) -> Dict[str, str]:

        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region_name)

        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        except ClientError as e:
            logging.error("Failed to retrieve secret: %s", e)
            raise e

        return json.loads(get_secret_value_response['SecretString'])
