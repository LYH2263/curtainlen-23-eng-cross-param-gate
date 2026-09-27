from app.db import connect

def list_windows():
    c = connect()
    try:
        return [dict(r) for r in c.execute("SELECT * FROM windows ORDER BY id").fetchall()]
    finally:
        c.close()

def get_window(wid: int):
    c = connect()
    try:
        r = c.execute("SELECT * FROM windows WHERE id=?", (wid,)).fetchone()
        return dict(r) if r else None
    finally:
        c.close()

def update_window(wid: int, fields: dict):
    cols = {k: v for k, v in fields.items() if k in ("name", "width", "height", "fullness", "note")}
    if cols:
        c = connect()
        try:
            c.execute("UPDATE windows SET " + ",".join(f"{k}=?" for k in cols) + " WHERE id=?", (*cols.values(), wid))
            c.commit()
        finally:
            c.close()
    return get_window(wid)
