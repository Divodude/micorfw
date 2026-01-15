import asyncio
import json
from sqlalchemy import text
from main import app
from microfw.orm_db import Database
from microfw.middleware.db import DatabaseMiddleware
from microfw.response import Response
from microfw.asgi import ASGI

# 1. Setup Database
db = Database("sqlite+aiosqlite:///crud_test.db")
app.middleware(DatabaseMiddleware(db))

# 2. Lifecycle Hooks
@app.on_event("startup")
async def startup():
    print("Startup: Connecting to DB...")
    await db.connect()
    async with await db.session() as session:
        # Create Table
        await session.execute(text("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"))
        await session.commit()
    print("Startup: DB Initialized.")

@app.on_event("shutdown")
async def shutdown():
    print("Shutdown: Closing DB...")
    await db.disconnect()

# 3. CRUD Routes

# CREATE
@app.route("/items", methods=["POST"])
async def create_item(request):
    # For simplicity, assuming body is just the name string
    name = request.body.decode().strip()
    result = await request.db.execute(text("INSERT INTO items (name) VALUES (:name)"), {"name": name})
    await request.db.commit()
    # Get last inserted id (sqlite specific trick or generic)
    # SQLAlchemy cursor result usually has .lastrowid
    new_id = result.lastrowid
    return Response(f"{new_id}", status_code=201)

# READ
@app.route("/items/{id}")
async def get_item(request, id):
    result = await request.db.execute(text("SELECT name FROM items WHERE id = :id"), {"id": id})
    row = result.fetchone()
    if row:
        return Response(row[0])
    return Response("Not Found", status_code=404)

# UPDATE
@app.route("/items/{id}/update", methods=["POST"]) # Using POST for update for simplicity if PUT not supported by logic yet (methods array default GET)
async def update_item(request, id):
    new_name = request.body.decode().strip()
    result = await request.db.execute(text("UPDATE items SET name = :name WHERE id = :id"), {"name": new_name, "id": id})
    await request.db.commit()
    if result.rowcount > 0:
        return Response("Updated")
    return Response("Not Found", status_code=404)

# DELETE
@app.route("/items/{id}/delete", methods=["POST"]) # POST for delete execution
async def delete_item(request, id):
    result = await request.db.execute(text("DELETE FROM items WHERE id = :id"), {"id": id})
    await request.db.commit()
    if result.rowcount > 0:
        return Response("Deleted")
    return Response("Not Found", status_code=404)


# 4. Test Runner
async def run_tests():
    runner = ASGI(app)
    
    # Helper to send requests
    async def make_request(method, path, body=b""):
        print(f"\n> {method} {path} body={body}")
        
        response_data = {"status": None, "body": b""}
        
        scope = {
            "type": "http",
            "method": method,
            "path": path,
            "query_string": b"",
            "headers": [],
        }
        
        async def receive():
            return {"type": "http.request", "body": body}
        
        async def send(msg):
            if msg["type"] == "http.response.start":
                response_data["status"] = msg["status"]
            elif msg["type"] == "http.response.body":
                response_data["body"] += msg["body"]

        await runner(scope, receive, send)
        print(f"< Status: {response_data['status']}, Body: {response_data['body'].decode()}")
        return response_data

    # --- Execution ---
    
    # Manually trigger startup (simulating Uvicorn)
    for handler in app.startup_handlers:
        await handler()

    try:
        # 1. Create
        resp = await make_request("POST", "/items", b"Milk")
        item_id = resp["body"].decode()
        assert resp["status"] == 201
        
        # 2. Read
        resp = await make_request("GET", f"/items/{item_id}")
        assert resp["status"] == 200
        assert resp["body"].decode() == "Milk"
        
        # 3. Update
        await make_request("POST", f"/items/{item_id}/update", b"Dark Milk")
        
        # Verify Update
        resp = await make_request("GET", f"/items/{item_id}")
        assert resp["body"].decode() == "Dark Milk"
        
        # 4. Delete
        await make_request("POST", f"/items/{item_id}/delete")
        
        # Verify Delete
        resp = await make_request("GET", f"/items/{item_id}")
        assert resp["status"] == 404
        
        print("\nAll CRUD tests PASSED!")

    finally:
        # Manually trigger shutdown
        for handler in app.shutdown_handlers:
            await handler()

if __name__ == "__main__":
    asyncio.run(run_tests())
