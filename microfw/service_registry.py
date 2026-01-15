class ServiceRegistry:
    def __init__(self):
        self._services = {}

    def register(self, name: str, base_url: str):
        self._services[name] = base_url.rstrip("/")

    def get_url(self, name: str) -> str:
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found in registry.")
        return self._services[name]
