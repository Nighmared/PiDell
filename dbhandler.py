import sqlite3


class Dbhandler:
    def __init__(self, fpath):
        self.fpath = fpath

    def get_admins(self):
        conn = sqlite3.connect(self.fpath)
        curs = conn.cursor()
        curs.execute("SELECT uid FROM admins")
        res = curs.fetchall()
        conn.close()
        return map(lambda x: int(x[0]), res)

    def add_admin(self, uid: int):
        conn = sqlite3.connect(self.fpath)
        curs = conn.cursor()
        curs.execute("""INSERT INTO admins(uid) VALUES(?)""", (uid,))
        conn.commit()
        conn.close()

    def del_admin(self, uid: int):
        conn = sqlite3.connect(self.fpath)
        curs = conn.cursor()
        curs.execute("""DELETE FFROM admins WHERE uid=?""", (uid,))
        conn.commit()
        conn.close()
