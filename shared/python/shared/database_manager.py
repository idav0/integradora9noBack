import os
import pymysql
import logging


class DatabaseConfig:
    def __init__(self):

        self.__mysql_host = os.getenv("RDS_HOST")
        self.__mysql_db = os.getenv("RDS_DB")
        self.__mysql_user = os.getenv("RDS_USER")
        self.__mysql_password = os.getenv("RDS_PASSWORD")

    def __create_connection(self):
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
