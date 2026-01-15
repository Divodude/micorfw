import asyncio
import json
from microfw.app import App
from microfw.request import Request
from microfw.serializers import BaseModel, ValidationError

# --- Setup ---
app = App()

class Item(BaseModel):
    name: str
    price: int

@app.route("/items", methods=["POST"])
async def create_item(item: Item):
    return item

@app.route("/items_dict", methods=["POST"])
async def create_item_dict(item: Item):
    return {"message": "success", "item": item.model_dump()}

# --- Test Runner ---
async def run_tests():
    print("Running Pydantic Integration Tests...")
    
    # Test 1: Valid Request -> Automatic Injection & Serialization
    print("\nTest 1: Valid Request")
    body = json.dumps({"name": "Milk", "price": 10})
    req = Request("/items", "POST", body=body)
    resp = await app.dispatch(req)
    
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.data}")
    
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/json"
    data = json.loads(resp.data)
    assert data["name"] == "Milk"
    assert data["price"] == 10
    
    # Test 2: Invalid Request (Validation Error)
    print("\nTest 2: Invalid Request (Wrong Type)")
    body = json.dumps({"name": "Milk", "price": "ten"}) # Price should be int
    req = Request("/items", "POST", body=body)
    resp = await app.dispatch(req)
    
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.data}")
    
    assert resp.status_code == 422
    assert "error" in json.loads(resp.data)

    # Test 3: Invalid JSON
    print("\nTest 3: Invalid JSON Body")
    body = "{invalid_json"
    req = Request("/items", "POST", body=body)
    resp = await app.dispatch(req)
    
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.data}")
    
    assert resp.status_code == 400

    print("\nAll Pydantic tests PASSED!")

if __name__ == "__main__":
    asyncio.run(run_tests())
