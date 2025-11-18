import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import BeeProduct, Order

app = FastAPI(title="Bee Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Bee Store API is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Welcome to the Bee Store"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# --------- Bee products endpoints ---------

@app.get("/api/products")
def list_products():
    docs = get_documents("beeproduct")
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["_id"] = str(d["_id"])
    return {"products": docs}


@app.post("/api/products", status_code=201)
def create_product(product: BeeProduct):
    inserted_id = create_document("beeproduct", product)
    return {"id": inserted_id}


@app.post("/api/seed")
def seed_products():
    """Seed the database with default bee products if none exist."""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    count = db["beeproduct"].count_documents({})
    if count > 0:
        return {"message": "Products already seeded", "count": count}

    defaults = [
        {
            "name": "Italian Honey Bees (Nucleus)",
            "species": "Apis mellifera ligustica",
            "description": "Gentle temperament, great honey production. 5-frame nuc with marked queen.",
            "price": 185.0,
            "image": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1200&auto=format&fit=crop",
            "in_stock": True,
        },
        {
            "name": "Carniolan Package Bees",
            "species": "Apis mellifera carnica",
            "description": "Fast spring buildup and overwintering success. 3 lb package with mated queen.",
            "price": 165.0,
            "image": "https://images.unsplash.com/photo-1470115636492-6d2b56f9146e?q=80&w=1200&auto=format&fit=crop",
            "in_stock": True,
        },
        {
            "name": "Saskatraz Queens",
            "species": "Apis mellifera",
            "description": "Selected for mite tolerance and productivity. Marked, mated queen ready to introduce.",
            "price": 42.0,
            "image": "https://images.unsplash.com/photo-1510877073473-6d4545e9c7e1?q=80&w=1200&auto=format&fit=crop",
            "in_stock": True,
        },
        {
            "name": "Native Bumblebee Colony",
            "species": "Bombus impatiens",
            "description": "Excellent greenhouse pollinators. Complete colony with queen and workers.",
            "price": 299.0,
            "image": "https://images.unsplash.com/photo-1461354464878-ad92f492a5a0?q=80&w=1200&auto=format&fit=crop",
            "in_stock": False,
        },
    ]

    inserted = 0
    for p in defaults:
        try:
            inserted_id = create_document("beeproduct", p)
            if inserted_id:
                inserted += 1
        except Exception:
            pass

    return {"message": "Seeded products", "count": inserted}


# --------- Orders endpoints ---------

@app.post("/api/orders", status_code=201)
def create_order(order: Order):
    # Verify product ids exist
    for item in order.items:
        try:
            found = db["beeproduct"].find_one({"_id": ObjectId(item.product_id)})
            if found is None:
                raise HTTPException(status_code=400, detail=f"Product not found: {item.product_id}")
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid product id: {item.product_id}")

    inserted_id = create_document("order", order)
    return {"id": inserted_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
