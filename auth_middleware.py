from microfw.middleware import Middleware
from microfw.response import Response

class AuthMiddleware(Middleware):
    async def __call__(self, request, call_next):
        # Implement your authentication logic here
        # For example, check for a valid token in the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response("Unauthorized", status_code=401)
        
        # If authentication is successful, call the next middleware
        return await call_next(request)

if __name__ == "__main__":
    print("Verifying AuthMiddleware...")
    assert issubclass(AuthMiddleware, Middleware)
    print("AuthMiddleware inherits from Middleware successfully.")
    
    # helper mock
    async def mock_next(req):
        return "OK"
    
    class MockRequest:
        headers = {}
        
    import asyncio
    
    async def test():
        mw = AuthMiddleware()
        # Test fail
        req_fail = MockRequest()
        res_fail = await mw(req_fail, mock_next)
        assert res_fail.status_code == 401
        print("AuthMiddleware denied execution as expected.")
        
        # Test success
        req_ok = MockRequest()
        req_ok.headers = {"Authorization": "Bearer token"}
        res_ok = await mw(req_ok, mock_next)
        assert res_ok == "OK"
        print("AuthMiddleware allowed execution as expected.")
        
    asyncio.run(test())
