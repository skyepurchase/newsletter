from getpass import getpass
from argparse import ArgumentParser

import mysql.connector

from utils import hash_passcode


if __name__=='__main__':
    parser = ArgumentParser("Create Newsletter")
    parser.add_argument("--title", help="The title of the newsletter")

    args = parser.parse_args()
    passcode = getpass("Passcode: ")
    pass_hash = hash_passcode(passcode)

    db_passwd = getpass("Database password: ")

    mydb = mysql.connector.connect(
        host="localhost",
        user="atp45",
        password=db_passwd,
        database="atp45/newsletter"
    )

    mycursor = mydb.cursor()

    sql = "INSERT INTO newsletters (title, passcode) VALUES (%s, %s);"
    val = (args.title, pass_hash)
    mycursor.execute(sql, val)

    mydb.commit()
