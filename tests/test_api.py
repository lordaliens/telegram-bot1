import unittest
import os
from fastapi.testclient import TestClient
from app import app
from database import poweryoga_db

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.db_name = "poweryoga.db"
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
        poweryoga_db.init_db(self.db_name)
        self.client = TestClient(app)

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_client_crud_and_ai_generation(self):
        # Create client
        c_data = {
            "first_name": "نیلوفر",
            "last_name": "نوری",
            "age": 27,
            "height": 170.0,
            "weight": 62.0,
            "training_history": "۶ ماه یوگا"
        }
        res = self.client.post("/api/clients", json=c_data)
        self.assertEqual(res.status_code, 200)
        client_id = res.json()["id"]

        # Get clients list
        res = self.client.get("/api/clients")
        self.assertEqual(res.status_code, 200)
        clients = res.json()
        self.assertEqual(len(clients), 1)

        # Add progress
        p_data = {"weight": 60.8, "notes": "کاهش وزن شگفت‌انگیز"}
        res = self.client.post(f"/api/clients/{client_id}/progress", json=p_data)
        self.assertEqual(res.status_code, 200)

        # Generate AI Plan
        res = self.client.post(f"/api/clients/{client_id}/generate-plan", json={"plan_type": "combined"})
        self.assertEqual(res.status_code, 200)
        plan_data = res.json()
        self.assertIn("پاور یوگا", plan_data["content"])

        # Fetch client plans
        res = self.client.get(f"/api/clients/{client_id}/plans")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)

if __name__ == "__main__":
    unittest.main()
