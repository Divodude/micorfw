import uuid
from microfw.context import RequestContext
from microfw.client import ServiceClient

class ContextMiddleware:
    def __init__(self, service_registry, service_name="microfw-service"):
        self.service_registry = service_registry
        self.service_name = service_name

    async def __call__(self, request, call_next):
        # 1. Trace ID
        trace_id = request.header.get("x-trace-id")
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        # 2. Span ID (We are a new span in this trace)
        span_id = str(uuid.uuid4())

        # 3. Create Context
        context = RequestContext(
            trace_id=trace_id,
            span_id=span_id, # This is OUR span ID.
            service_name=self.service_name
        )

        # 4. Attach to Request
        request.context = context
        request.client = ServiceClient(context, self.service_registry)

        return await call_next(request)
