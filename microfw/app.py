from microfw.exceptions import HTTPException
from microfw.response import Response
try:
    from microfw.serializers import BaseModel, ValidationError
except ImportError:
    BaseModel = None
    ValidationError = None

import re
from microfw.service_registry import ServiceRegistry
from microfw.middleware.context import ContextMiddleware
from microfw.settings import settings

class App:
    def __init__(self):
        self.routes = {}
        self.dynamic_routes = []
        self.middlewares = []
        self.startup_handlers = []
        self.shutdown_handlers = []
        self.services = ServiceRegistry()
        # Add ContextMiddleware as the VERY FIRST middleware so it runs first
        self.middlewares.append(ContextMiddleware(self.services, service_name=settings.SERVICE_NAME))

    def on_event(self, event_type):
        def wrapper(func):
            if event_type == "startup":
                self.startup_handlers.append(func)
            elif event_type == "shutdown":
                self.shutdown_handlers.append(func)
            return func
        return wrapper

    def add_service(self, name: str, base_url: str):
        self.services.register(name, base_url)

    def route(self, path, methods=["GET"], middlewares=None):
        def wrapper(func):
            for method in methods:
                # Check for path parameters, e.g., /users/{id}
                if '{' in path and '}' in path:
                    # Convert /users/{id} to ^/users/(?P<id>[^/]+)$
                    # Escape the path first, then replace \{(\w+)\} with (?P<\1>[^/]+)
                    # Note: We need to handle slashes correctly.
                    # Simple approach: replace {var} with (?P<var>[^/]+)
                    regex_path = "^" + path + "$"
                    regex_path = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', regex_path)
                    
                    self.dynamic_routes.append({
                        "method": method.upper(),
                        "regex": re.compile(regex_path),
                        "handler": func,
                        "middlewares": middlewares
                    })
                else:
                    key = (method.upper(), path)
                    self.routes[key] = {"handler": func, "middlewares": middlewares}
            return func
        return wrapper

    def middleware(self, func):
        self.middlewares.append(func)
        return func


    async def dispatch(self, request):
        key = (request.method.upper(), request.path)
        
        handler_func = None
        route_middlewares = []
        kwargs = {}

        # 1. Route Lookup
        if key in self.routes:
            # Exact match
            route_info = self.routes[key]
            handler_func = route_info["handler"]
            route_middlewares = route_info["middlewares"] or []
        else:
            # Dynamic match
            for route in self.dynamic_routes:
                if route["method"] == request.method.upper():
                    match = route["regex"].match(request.path)
                    if match:
                        handler_func = route["handler"]
                        route_middlewares = route["middlewares"] or []
                        kwargs = match.groupdict()
                        break
        
        if not handler_func:
            # 404 Handler
            class NotFoundResponse:
                status_code = 404
                headers = {}
                data = "404 Not Found"
            return NotFoundResponse()

        # 2. Define the base handler (the route function itself)
        async def base_handler(req, **route_args):
            import inspect
            sig = inspect.signature(handler_func)
            
            # Determine arguments to pass
            # Determine arguments to pass
            pass_args = {}
            
            # --- Pydantic Injection Logic ---
            if BaseModel:
                # Look for a parameter annotated with a subclass of BaseModel
                for name, param in sig.parameters.items():
                    if isinstance(param.annotation, type) and issubclass(param.annotation, BaseModel):
                        # Found a model! Parse body.
                        try:
                            body_data = await req.json()
                            model_instance = param.annotation(**body_data)
                            pass_args[name] = model_instance
                        except ValidationError as e:
                            # Return 400/422 on validation error
                            return Response(data={"error": e.errors()}, status_code=422, headers={"Content-Type": "application/json"})
                        except Exception as e:
                             return Response(data={"error": "Invalid JSON body"}, status_code=400)
            # --------------------------------

            if len(sig.parameters) > 0:
                # Check if 'request' is in parameters
                if 'request' in sig.parameters:
                    pass_args['request'] = req
                
                # Pass route_args if they exist in signature
                for name, value in route_args.items():
                    if name in sig.parameters:
                        pass_args[name] = value

            if inspect.iscoroutinefunction(handler_func):
                result = await handler_func(**pass_args)
            else:
                result = handler_func(**pass_args)
            
            # --- Pydantic Response Logic ---
            if BaseModel and isinstance(result, BaseModel):
                 return Response(data=result.model_dump(), status_code=200, headers={"Content-Type": "application/json"})
            
            if isinstance(result, dict) or isinstance(result, list):
                 return Response(data=result)
            
            return result


        # 3. Combine Middlewares (Global + Route-specific)
        all_middlewares = self.middlewares + route_middlewares

        # 4. Build Chain
        handler = base_handler
        for middleware in reversed(all_middlewares):
            async def wrapped(req, m=middleware, next_handler=handler):
                import inspect
                # Middleware doesn't usually take route_args directly from signature?
                # The way 'call_next(request)' works, it passes request.
                # But 'handler' (base_handler) needs 'kwargs'.
                # We need to bind 'kwargs' to 'base_handler' or pass them through.
                # Standard ASGI middleware just takes scope/receive/send or Request.
                # Our middleware signature is (request, call_next).
                # So call_next(request) calls next_handler(request).
                # So 'next_handler' must accept 'request'. 
                # References to 'kwargs' must be captured by 'base_handler'.
                
                # We handle this by creating a partial for the next handler if needed?
                # Actually, 'base_handler' above takes (req, **route_args).
                # But 'wrapped' calls 'next_handler(req)'.
                # So we must partial 'kwargs' into 'base_handler' BEFORE wrapping?
                # YES.
                
                if inspect.iscoroutinefunction(m):
                   return await m(req, next_handler)
                else:
                   return m(req, next_handler)
            handler = wrapped

        
        actual_base = handler
        if handler == base_handler:
             # If no middlewares, we just call base_handler(request, **kwargs)
             # But wait, middleware chain expects 'next_handler' to take 1 arg (request).
             # So 'base_handler' should be (req).
             # Let's redefine base_handler to capture kwargs from closure.
             pass

        # 5. Execute with Error Handling
        try:
            # We need to adapt base_handler to only take 'req' and use 'kwargs' from closure.
            async def base_handler_closure(req):
                 return await base_handler(req, **kwargs)

            # Rebuild chain with closure
            handler = base_handler_closure
            for middleware in reversed(all_middlewares):
                async def wrapped(req, m=middleware, next_handler=handler):
                    import inspect
                    
                    # Call the middleware
                    # Middleware signature: (request, call_next)
                    result = m(req, next_handler)
                    
                    if inspect.isawaitable(result):
                        return await result
                    return result
                handler = wrapped

            return await handler(request)
        except HTTPException as e:
            return Response(data=e.detail, status_code=e.status_code, headers=e.headers)
        except Exception as e:
            # Fallback for other errors
            print(f"Internal Server Error: {e}")
            import traceback
            traceback.print_exc()
            return Response(data="Internal Server Error", status_code=500)
