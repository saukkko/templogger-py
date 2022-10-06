from sqlite3 import connect, Connection
from datetime import datetime


def get_now():
    return datetime.utcnow().timestamp().__trunc__()


def init_db(db_path: str):
    db = connect(db_path)
    c = db.cursor()
    sql1 = """CREATE TABLE IF NOT EXISTS "users" (
        "id"            INTEGER     NOT NULL UNIQUE,
        "username"      TEXT        NOT NULL UNIQUE,
        "hash"          TEXT        NOT NULL,

        PRIMARY KEY("id" AUTOINCREMENT)
    );"""
    sql2 = """CREATE TABLE IF NOT EXISTS "tokens" (
        "id"            INTEGER     NOT NULL UNIQUE,
        "user_id"       INTEGER     NOT NULL UNIQUE,
        "expires"       INTEGER     NOT NULL,
        "thumbprint"    TEXT        NOT NULL UNIQUE,
        
        FOREIGN KEY("user_id") REFERENCES "users",
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    """
    c = c.execute(sql1)
    c = c.execute(sql2)
    c.close()
    db.commit()

    return db


def get_user(db: Connection, username: str) -> str:
    c = db.cursor()
    c.execute(f'SELECT "hash" FROM "users" WHERE "username" = ?;', [username])
    r = c.fetchone()
    if r and len(r) > 0:
        return str(r[0])
    return ""


# WIP
def update_token(db: Connection, username: str, token_expiry: int, thumbprint: str):
    c = db.cursor()
    c.execute(f'SELECT "expires" FROM "tokens" WHERE "thumbprint = ?";', [thumbprint])
    r = c.fetchone()
    now = get_now()

    if not r or now >= int(r[0]):
        c.execute(f'SELECT "user_id" FROM "users" WHERE "username" = ?;', [username])
        user_id = str(c.fetchone()[0])
        c.execute(f'INSERT OR REPLACE INTO "tokens" ("user_id", "expires", "thumbprint") VALUES (?, ?, ?)',
                  [user_id, token_expiry, thumbprint])
    else:
        c.execute(f'SELECT "expires" FROM "tokens" WHERE "user_id" = ?;')
        r = c.fetchone()
        if not r:
            raise ValueError("Result set was empty when it should not be")

# print(get_user(db, "demo_user"))

