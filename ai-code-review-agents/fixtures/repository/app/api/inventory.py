
from fastapi import FastAPI, Depends, HTTPException
from app.auth import get_current_user
from app.models import User
from app import db

app = FastAPI()


@app.post("/api/inventory/{item_id}/reserve")
def reserve_inventory(item_id: int, quantity: int, current_user: User = Depends(get_current_user)):
    with db.transaction():
        item = db.query(
            "SELECT * FROM inventory WHERE id = ? FOR UPDATE",
            (item_id,)
        )
        if not item or item.quantity < quantity:
            raise HTTPException(status_code=400, detail="Insufficient inventory")
        db.execute(
            "UPDATE inventory SET quantity = quantity - ? WHERE id = ?",
            (quantity, item_id)
        )
        return {"status": "reserved", "remaining": item.quantity - quantity}
