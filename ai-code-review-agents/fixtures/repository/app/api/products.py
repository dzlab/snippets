
from fastapi import FastAPI, Request
from app.auth import limiter
from app import db

app = FastAPI()


@app.get("/api/products/search")
@limiter.limit("20/minute")
def search_products(request: Request, name: str, category: str):
    results = db.execute(
        "SELECT * FROM products WHERE name LIKE ? AND category = ?",
        (f"%{name}%", category)
    )
    return results
