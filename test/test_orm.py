from main import app
import asyncio
from microfw.orm_db import Database
from microfw.middleware.db import DatabaseMiddleware
from microfw.response import Response
from microfw.request import Request
from sqlalchemy import text

# Setup DB
db = Database("sqlite+aiosqlite:///test.db")
app.middleware(DatabaseMiddleware(db))

@app.on_event("startup")
async def startup():
    await db.connect()
    # Create table if not exists (using raw sql for test simplicity)
    async with await db.session() as session:
        await session.execute(text("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)"))
        await session.commit()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

@app.route("/db-test")
async def db_test(request):
    # Insert
    await request.db.execute(text("INSERT INTO test (name) VALUES ('Test Item')"))
    await request.db.commit()
    
    # Select
    result = await request.db.execute(text("SELECT name FROM test ORDER BY id DESC LIMIT 1"))
    name = result.scalar()
    return Response(f"DB Item: {name}")

# Test Runner
async def test():
    from microfw.asgi import ASGI
    runner = ASGI(app)
    
    print("--- Starting DB Test ---")
    
    # Simulate Lifecycle Startup
    scope_lifespan = {"type": "lifespan"}
    queue = asyncio.Queue()
    await queue.put({"type": "lifespan.startup"})
    
    async def receive_lifespan():
        return await queue.get()
    async def send_lifespan(msg):
        if msg["type"] == "lifespan.startup.complete":
            print("Startup Complete")
            
    # We need to run lifespan in background?
    # Or just manually call startup/shutdown handlers for this test script to keep it simple.
    # But we want to test middleware integration which relies on the app structure.
    # Middleware is added. Startup handlers need to run to connect DB.
    
    # Manual startup for test script simplicity
    await startup()
    
    # Simulate Request
    req_scope = {
        "type": "http",
        "method": "GET",
        "path": "/db-test",
        "query_string": b"",
        "headers": []
    }
    
    async def receive_http():
        return {"type": "http.request", "body": b""}
        
    async def send_http(msg):
        if msg["type"] == "http.response.body":
            print(f"Response Body: {msg['body'].decode()}")
            
    print("Sending Request...")
    await runner(req_scope, receive_http, send_http)
    
    # Manual shutdown
    await shutdown()
    print("--- DB Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test())
