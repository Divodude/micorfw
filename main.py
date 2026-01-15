from microfw.app import App
from microfw.request import Request
from microfw.response import Response
from microfw.asgi import ASGI
from microfw.orm_db import Database
from microfw.middleware.db import DatabaseMiddleware
from microfw.middleware.transaction import TransactionMiddleware
from microfw.middleware.concurrency import ConcurrencyMiddleware
from microfw.model import Base
from sqlalchemy import select, String
from sqlalchemy.orm import Mapped, mapped_column


app = App()


app.middleware(ConcurrencyMiddleware(limit=125, max_wait=0.1)) # Fail fast!
db = Database("sqlite+aiosqlite:///crud_test.db")
app.middleware(DatabaseMiddleware(db))
app.middleware(TransactionMiddleware())

@app.route("/", methods=["GET"])
def index():
    return Response("MicroFW is running. Available via /items", status_code=200)

# 2. Define Model
class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    def __repr__(self):
        return f"<Item {self.name}>"

# 3. Lifecycle Hooks
@app.on_event("startup")
async def startup():
    print("Startup: Connecting to DB...")
    await db.connect()
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Startup: DB Initialized.")

@app.on_event("shutdown")
async def shutdown():
    print("Shutdown: Closing DB...")
    await db.disconnect()

# 4. CRUD Routes

# CREATE


@app.route("/items", methods=["POST", "GET"])
async def create_item(request):
    if request.method == "GET":
        result = await request.db.execute(select(Item))
        items = result.scalars().all()
        # Serialize list of objects to list of dicts
        data = [{"id": i.id, "name": i.name} for i in items]
        return Response(data, status_code=200)

    if request.method == "POST":
        # Parse JSON body
        data = await request.json()
        name = data.get("name")
        if not name:
             return Response({"error": "Name is required"}, status_code=400)
             
        new_item = Item(name=name)
        request.db.add(new_item)
        await request.db.commit()
        await request.db.refresh(new_item)
        return Response({"id": new_item.id, "name": new_item.name}, status_code=201)

# READ
@app.route("/items/{id}")
async def get_item(request, id):
    result = await request.db.execute(select(Item).where(Item.id == int(id)))
    item = result.scalar_one_or_none()
    if item:
        return Response(item.name)
    return Response("Not Found", status_code=404)

# UPDATE
@app.route("/items/{id}/update", methods=["POST"])
async def update_item(request, id):
    new_name = request.body.decode().strip()
    result = await request.db.execute(select(Item).where(Item.id == int(id)))
    item = result.scalar_one_or_none()
    if item:
        item.name = new_name
        await request.db.commit()
        return Response("Updated")
    return Response("Not Found", status_code=404)


@app.route("/items/{id}/delete", methods=["POST"], middlewares=[TransactionMiddleware()])
async def delete_item(request, id):
    result = await request.db.execute(select(Item).where(Item.id == int(id)))
    item = result.scalar_one_or_none()
    if item:
        await request.db.delete(item)
        await request.db.commit()
        return Response("Deleted")
    return Response("Not Found", status_code=404)






asgi = ASGI(app)

if __name__=="__main__":
    # When running uvicorn, point it to 'main:asgi'
    pass
    