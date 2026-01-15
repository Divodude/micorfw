import asyncio
import time
from unittest.mock import MagicMock, patch
from microfw.app import App
from microfw.response import Response
from microfw.client import ServiceClient
from microfw.context import RequestContext
from microfw.exceptions import HTTPException

# Mock App setup
app = App()
app.add_service("user-service", "http://user-service.internal")

async def run_tests():
    print("Running Service Client Verification...")

    # 1. Test Service Registry
    print("\n[1] Testing Service Registry...")
    try:
        url = app.services.get_url("user-service")
        assert url == "http://user-service.internal"
        print("PASS: Service resolved correctly.")
    except Exception as e:
        print(f"FAIL: {e}")

    try:
        app.services.get_url("unknown")
        print("FAIL: Should have raised ValueError for unknown service")
    except ValueError:
        print("PASS: Unknown service raised ValueError.")

    # 2. Test Client Logic (Trace & Timeout)
    print("\n[2] Testing Client Logic...")
    
    # Mock Context
    trace_id = "test-trace-123"
    span_id = "test-span-456"
    deadline = time.time() + 1.0 # 1s remaining
    context = RequestContext(
        trace_id=trace_id,
        span_id=span_id,
        deadline=deadline,
        service_name="test-runner"
    )
    
    client = ServiceClient(context, app.services)

    # Mock httpx.AsyncClient
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_instance
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1}
        
        # Async mock for request
        async def mock_request(*args, **kwargs):
            return mock_response
        mock_instance.request.side_effect = mock_request

        # A. Happy Path
        print("  A. Happy Path Request")
        await client.get("user-service", "/users/1")
        
        # Verify call arguments
        call_args = mock_instance.request.call_args
        # method, url, kwargs
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "http://user-service.internal/users/1"
        headers = call_args[1]["headers"]
        assert headers["X-Trace-ID"] == trace_id
        assert headers["X-Parent-Span"] == span_id
        print("PASS: URL resolved and Headers injected.")

        # B. Timeout Enforcement (Pre-check)
        print("  B. Timeout Enforcement")
        context.deadline = time.time() - 1.0 # Expired
        try:
            await client.get("user-service", "/foo")
            print("FAIL: Should have raised Timeout (HTTPException 504)")
        except HTTPException as e:
            if e.status_code == 504:
                print("PASS: Deadline exceeded raised 504.")
            else:
                print(f"FAIL: Raised wrong status {e.status_code}")

        # Reset deadline
        context.deadline = time.time() + 5.0

        # C. 5xx Error Handling
        print("  C. 5xx Error Handling")
        mock_response.status_code = 500
        try:
            await client.get("user-service", "/error")
            print("FAIL: Should have raised 502 for 500 response")
        except HTTPException as e:
            if e.status_code == 502:
                print("PASS: 500 response raised 502.")
            else:
                print(f"FAIL: Raised wrong status {e.status_code}")

    print("\nVerification Complete.")

if __name__ == "__main__":
    asyncio.run(run_tests())
