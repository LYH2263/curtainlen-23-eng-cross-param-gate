from app.db import connect

def list_fabrics():
    c = connect()
    try:
        return [dict(r) for r in c.execute("SELECT * FROM fabrics ORDER BY id").fetchall()]
    finally:
        c.close()

def get_fabric(fid: int):
    c = connect()
    try:
        r = c.execute("SELECT * FROM fabrics WHERE id=?", (fid,)).fetchone()
        return dict(r) if r else None
    finally:
        c.close()

UPDATABLE = ("fabric_width", "hem_top", "hem_bottom", "note")

def update_fabric(fid: int, fields: dict):
    sets = {k: v for k, v in fields.items() if k in UPDATABLE and v is not None}
    if sets:
        c = connect()
        try:
            cur = c.execute(
                "UPDATE fabrics SET " + ",".join(f"{k}=?" for k in sets) + " WHERE id=?",
                (*sets.values(), fid),
            )
            c.commit()
            if cur.rowcount == 0:
                return None
        finally:
            c.close()
    return get_fabric(fid)
