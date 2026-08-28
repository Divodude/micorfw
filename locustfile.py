"""from locust import HttpUser, task, between

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
"""
from locust import HttpUser, task, between
import random

class ArogyaRxUser(HttpUser):
    # Update this with your server's base URL
    host = "http://127.0.0.1:5000"
    
    # Simulate real users waiting between requests
    wait_time = between(0.5, 2.5)
    
    # Common headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    def on_start(self):
        """Called when a user starts the test"""
        # You can add authentication here if needed
        # self.login()
        pass
    
    # High frequency endpoints (weight=3)
    @task(3)
    def get_products(self):
        """Test product listing"""
        self.client.get("/api/products/", headers=self.headers)
        
    @task(3)
    def get_product_categories(self):
        """Test category listing"""
        self.client.get("/api/categories/", headers=self.headers)
    
    # Medium frequency endpoints (weight=2)
    @task(2)
    def get_product_detail(self):
        """Test product detail view"""
        # Assuming product IDs are between 1-100
        product_id = random.randint(1, 100)
        self.client.get(f"/api/products/{product_id}/", headers=self.headers)
    
    @task(2)
    def search_products(self):
        """Test search functionality"""
        search_terms = ["medicine", "health", "vitamin", "pain", "cold"]
        term = random.choice(search_terms)
        self.client.get(f"/api/products/?search={term}", headers=self.headers)
    
    # Low frequency endpoints (weight=1)
    @task(1)
    def create_order(self):
        """Test order creation"""
        order_data = {
            "items": [
                {"product_id": random.randint(1, 100), "quantity": random.randint(1, 5)}
                for _ in range(random.randint(1, 3))
            ],
            "shipping_address": "123 Test St, Test City",
            "payment_method": "COD"
        }
        self.client.post("/api/orders/", json=order_data, headers=self.headers)
    
    @task(1)
    def get_order_history(self):
        """Test order history"""
        self.client.get("/api/orders/", headers=self.headers)
    
    # Uncomment and modify if you have authentication
    # def login(self):
    #     response = self.client.post("/api/auth/login/", json={
    #         "username": "testuser",
    #         "password": "testpassword"
    #     })
    #     if response.status_code == 200:
    #         self.headers["Authorization"] = f"Bearer {response.json().get('access')}"