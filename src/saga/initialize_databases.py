import sqlite3

database_types = ["users", "permissions", "quotas"]


def get_connection(db_type):
    return sqlite3.connect(f'db/{db_type}.db')


def initialize_database_by_type(db_types):
    for db_type in db_types:
        conn = get_connection(db_type)
        cursor = conn.cursor()

        if (db_type == "users"):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    processed INTEGER DEFAULT 0
                )
            ''')
        elif (db_type == "permissions"):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    permissions TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
        elif (db_type == "quotas"):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    storage_gb INTEGER,
                    ops_per_month INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

        conn.commit()
        conn.close()


if __name__ == "__main__":
    print("=====Inicializando bases de datos=====")
    initialize_database_by_type(database_types)
    print("Bases de datos inicializadas correctamente.")
