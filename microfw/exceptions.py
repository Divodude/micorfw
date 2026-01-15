class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = None, headers: dict = None):
        self.status_code = status_code
        self.detail = detail or "Error"
        self.headers = headers or {}
