from fastapi import FastAPI, HTTPException
import psycopg2
import os

app = FastAPI()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "database"),
            database=os.environ.get("DB_NAME", "commerce"),
            user=os.environ.get("DB_USER", "admin"),
            password=os.environ.get("DB_PASS", "password")
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/products")
def get_products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price FROM products;")
    products = [{"id": row[0], "name": row[1], "price": float(row[2])} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return {"products": products}

@app.get("/health")
def health():
    return {"status": "api_is_running"}
