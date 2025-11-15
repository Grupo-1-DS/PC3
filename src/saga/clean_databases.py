
import sqlite3

db_names = ["users", "permissions", "quotas"]

def get_connection(db_type):
        return sqlite3.connect(f'db/{db_type}.db')

def clean():

    for db_name in db_names:
        conn = get_connection(db_name)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {db_name};")
        conn.commit()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    clean()