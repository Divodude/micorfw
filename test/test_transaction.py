from microfw.app import App
from microfw.orm_db import Database
from microfw.middleware.db import DatabaseMiddleware
from microfw.middleware.transaction import TransactionMiddleware
from microfw.response import Response
from microfw.request import Request
from microfw.model import Base
from microfw.asgi import ASGI
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
import asyncio

# Setup Logic
app = App()
db = Database("sqlite+aiosqlite:///status_test.db")
app.middleware(DatabaseMiddleware(db))
app.middleware(TransactionMiddleware())

class StatusItem(Base):
    __tablename__ = "status_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)

@app.on_event("startup")
async def startup():
    await db.connect()
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

@app.route("/success", methods=["POST"])
async def success_route(request):
    item = StatusItem(name="SuccessItem")
    request.db.add(item)
    # No explicit commit here! Middleware should do it.
    return Response("OK")

@app.route("/fail", methods=["POST"])
async def fail_route(request):
    item = StatusItem(name="FailItem")
    request.db.add(item)
    # Middleware should rollback this
    raise ValueError("Oops")

async def test():
    runner = ASGI(app)
    # Start
    for h in app.startup_handlers: await h()
    
    async def mock_receive():
        return {"type": "http.request", "body": b""}
    async def mock_send(msg):
        pass

    try:
        # Test 1: Success (Commit)
        print("Test 1: Success Route")
        scope = {"type":"http", "method":"POST", "path":"/success", "query_string":b"", "headers":[]}
        await runner(scope, mock_receive, mock_send)
        
        # Verify DB
        async with await db.session() as session:
            res = await session.execute(select(StatusItem).where(StatusItem.name == "SuccessItem"))
            item = res.scalar_one_or_none()
            if item:
                print("PASS: Item committed.")
            else:
                print("FAIL: Item NOT committed.")

        # Test 2: Failure (Rollback)
        print("\nTest 2: Failure Route")
        scope = {"type":"http", "method":"POST", "path":"/fail", "query_string":b"", "headers":[]}
        try:
             await runner(scope, mock_receive, mock_send)
        except ValueError:
             print("Caught expected error.")
             
        # Verify DB
        async with await db.session() as session:
            res = await session.execute(select(StatusItem).where(StatusItem.name == "FailItem"))
            item = res.scalar_one_or_none()
            if item:
                print("FAIL: Item committed despite error (Rollback failed).")
            else:
                print("PASS: Item NOT committed (Rollback success).")

    finally:
        for h in app.shutdown_handlers: await h()

if __name__ == "__main__":
    asyncio.run(test())
