import os
import contextlib
import time
from fastapi import FastAPI, HTTPException
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # If the database URL is missing, print a warning instead of crashing the container
    if not DATABASE_URL:
        print("WARNING: DATABASE_URL environment variable is not set. Database endpoints will fail.")
    else:
        conn = None
        for i in range(5):
            try:
                conn = psycopg.connect(DATABASE_URL)
                break
            except psycopg.OperationalError:
                print(f"Database not ready yet, retrying... ({i+1}/5)")
                time.sleep(2)
        
        if conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS items (
                            id SERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT
                        );
                    """)
                    conn.commit()
        else:
            print("Could not connect to the database.")
            # Do not raise a RuntimeError here for toy projects so the container stays running
            
    yield

app = FastAPI(lifespan=lifespan)


# --- CRUD ENDPOINTS ---

@app.post("/items")
def create_item(name: str, description: str = None):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id;",
                (name, description)
            )
            item_id = cur.fetchone()[0]
            conn.commit()
            return {"id": item_id, "name": name, "description": description}

@app.get("/items")
def read_all_items():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM items;")
            rows = cur.fetchall()
            return [{"id": r[0], "name": r[1], "description": r[2]} for r in rows]

@app.put("/items/{item_id}")
def update_item(item_id: int, name: str, description: str = None):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE items SET name = %s, description = %s WHERE id = %s RETURNING id;",
                (name, description, item_id)
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Item not found")
            conn.commit()
            return {"message": f"Item {item_id} updated successfully"}

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM items WHERE id = %s RETURNING id;", (item_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Item not found")
            conn.commit()
            return {"message": f"Item {item_id} deleted successfully"}
