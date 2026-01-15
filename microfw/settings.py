import os

class Settings:
    """
    Centralized settings for MicroFW.
    Values can be overridden by environment variables.
    """
    SERVICE_NAME = os.getenv("MICROFW_SERVICE_NAME", "microfw-app")
    
    # Concurrency Middleware Defaults
    CONCURRENCY_LIMIT = int(os.getenv("MICROFW_CONCURRENCY_LIMIT", "100"))
    CONCURRENCY_MAX_WAIT = float(os.getenv("MICROFW_CONCURRENCY_MAX_WAIT", "0.1"))
    
    # Debug Mode
    DEBUG = os.getenv("MICROFW_DEBUG", "False").lower() in ("true", "1", "yes")

settings = Settings()
