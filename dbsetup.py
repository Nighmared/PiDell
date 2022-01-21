import json
import sqlite3

# mapping from the required tables to the command used to create them.
required_tables = {
    "admins": """
    CREATE TABLE admins (uid INTEGER UNIQUE NOT NULL ,
    PRIMARY KEY(uid))
    """,
}


def setup(dbfile):

    conn = sqlite3.connect(dbfile)
    curs = conn.cursor()
    curs.execute("""SELECT name FROM sqlite_master WHERE type='table'""")

    fst = lambda a: a[0]
    res = list(map(fst, curs.fetchall()))
    new_table_created = False
    for table_name in required_tables:
        if table_name not in res:
            new_table_created = True
            print("creating table", table_name)
            curs.execute(required_tables[table_name])
        else:
            print(f"{table_name} already there")
    conn.commit()
    conn.close()
    return new_table_created
