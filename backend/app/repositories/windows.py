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

UPDATABLE = ("width", "height", "fullness", "note")

def update_window(wid: int, fields: dict):
    sets = {k: v for k, v in fields.items() if k in UPDATABLE and v is not None}
    if sets:
        c = connect()
        try:
            cur = c.execute(
                "UPDATE windows SET " + ",".join(f"{k}=?" for k in sets) + " WHERE id=?",
                (*sets.values(), wid),
            )
            c.commit()
            if cur.rowcount == 0:
                return None
        finally:
            c.close()
    return get_window(wid)
