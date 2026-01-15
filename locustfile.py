from locust import HttpUser, task, between

class MicroFWUser(HttpUser):
    host = "http://127.0.0.1:8001"

    # Simulates real users waiting between requests
    wait_time = between(0.01, 0.1)

    @task(3)
    def root(self):
        self.client.get("/")

    @task(1)
    def list_items(self):
        self.client.get("/items")
