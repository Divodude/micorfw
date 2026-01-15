from microfw.response import Response
from main import app
import asyncio
from microfw.request import Request

@app.route("/users/{id}")
def user_route(request, id):
    return Response(f"User ID: {id}", status_code=200)

@app.route("/items/{item_id}/details")
def item_details(item_id):
    return Response(f"Item: {item_id}", status_code=200)

async def test():
    print("Test 1: /users/123")
    req = Request("/users/123", "GET")
    resp = await app.dispatch(req)
    print(f"Result: {resp.data}")
    
    if resp.data == "User ID: 123":
        print("PASS")
    else:
        print("FAIL")

    print("\nTest 2: /items/abc/details")
    req = Request("/items/abc/details", "GET")
    resp = await app.dispatch(req)
    print(f"Result: {resp.data}")
    
    if resp.data == "Item: abc":
        print("PASS")
    else:
        print("FAIL")

if __name__ == "__main__":
    asyncio.run(test())
