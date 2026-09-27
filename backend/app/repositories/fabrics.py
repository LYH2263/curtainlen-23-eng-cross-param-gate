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

def update_fabric(fid: int, fields: dict):
    cols = {k: v for k, v in fields.items() if k in ("name", "fabric_width", "hem_top", "hem_bottom", "note")}
    if cols:
        c = connect()
        try:
            c.execute("UPDATE fabrics SET " + ",".join(f"{k}=?" for k in cols) + " WHERE id=?", (*cols.values(), fid))
            c.commit()
        finally:
            c.close()
    return get_fabric(fid)
