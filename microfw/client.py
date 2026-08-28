import httpx
import time
import asyncio
from typing import Any, Optional, Dict
from .context import RequestContext
from .service_registry import ServiceRegistry
from .exceptions import HTTPException

class ServiceClient:
    def __init__(self, context: RequestContext, registry: ServiceRegistry):
        self.context = context
        self.registry = registry

    async def _request(
        self, 
        method: str, 
        service: str, 
        path: str, 
        **kwargs
    ) -> Any:
        # 1. Resolve Service URL
        base_url = self.registry.get_url(service)
        url = f"{base_url}/{path.lstrip('/')}"

        # 2. Timeout Enforcement
        timeout = self.context.remaining_time()
        if timeout <= 0:
            raise HTTPException(status_code=504, detail="Request deadline exceeded before call")

        # 3. Trace Propagation
        headers = kwargs.get("headers", {})
        headers["X-Trace-ID"] = self.context.trace_id
        headers["X-Parent-Span"] = self.context.span_id
        # Also propagate context deadline if supported, logic varies, skipping for now
        kwargs["headers"] = headers

        # 4. Observability Hook (Start)
        start_time = time.time()
        
        max_retries = kwargs.pop("max_retries", 3)
        base_backoff = kwargs.pop("base_backoff", 0.5)

        try:
            for attempt in range(max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.request(method, url, **kwargs)
                        
                        # 5. Error Handling Rules
                        if response.status_code >= 500:
                            if response.status_code in (502, 503, 504) and attempt < max_retries:
                                # Transient error, allow retry loop to continue
                                pass
                            else:
                                raise HTTPException(status_code=502, detail=f"Upstream service '{service}' failed with {response.status_code}")
                        else:
                            return response

                except (httpx.TimeoutException, httpx.RequestError) as e:
                     if attempt == max_retries:
                         if isinstance(e, httpx.TimeoutException):
                             raise HTTPException(status_code=504, detail=f"Upstream service '{service}' timed out")
                         else:
                             raise HTTPException(status_code=502, detail=f"Connection to '{service}' failed: {str(e)}")
                
                # Backoff before next attempt
                if attempt < max_retries:
                    await asyncio.sleep(base_backoff * (2 ** attempt))

        finally:
            # Observability Hook (End)
            duration = time.time() - start_time
            self.context.spans.append({
                "service": service,
                "path": path,
                "method": method,
                "duration": duration,
                "status": locals().get("response", None) and locals()["response"].status_code or 0
            })

    async def get(self, service: str, path: str, **kwargs):
        return await self._request("GET", service, path, **kwargs)

    async def post(self, service: str, path: str, **kwargs):
        return await self._request("POST", service, path, **kwargs)

    async def put(self, service: str, path: str, **kwargs):
        return await self._request("PUT", service, path, **kwargs)

    async def delete(self, service: str, path: str, **kwargs):
        return await self._request("DELETE", service, path, **kwargs)
