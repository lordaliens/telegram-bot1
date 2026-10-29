import unittest
import os
from database import poweryoga_db

class TestPowerYogaDatabase(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_poweryoga_db.db"
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
        poweryoga_db.init_db(self.db_name)

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_add_and_get_client(self):
        cid = poweryoga_db.add_client(
            first_name="علی",
            last_name="حسینی",
            age=30,
            height=180.0,
            weight=80.0,
            training_history="سابقه تمرین بدنسازی",
            db_path=self.db_name
        )
        self.assertIsNotNone(cid)

        client = poweryoga_db.get_client_by_id(cid, db_path=self.db_name)
        self.assertEqual(client["first_name"], "علی")
        self.assertEqual(client["last_name"], "حسینی")
        self.assertEqual(client["weight"], 80.0)

    def test_add_progress(self):
        cid = poweryoga_db.add_client(
            first_name="مریم",
            last_name="احمدی",
            age=26,
            height=168.0,
            weight=65.0,
            training_history="",
            db_path=self.db_name
        )
        pid = poweryoga_db.add_progress(cid, 63.5, "پیشرفت ماه اول", db_path=self.db_name)
        self.assertIsNotNone(pid)

        progress = poweryoga_db.get_client_progress(cid, db_path=self.db_name)
        self.assertEqual(len(progress), 2)  # initial record + new record
        self.assertEqual(progress[1]["weight"], 63.5)

        updated_client = poweryoga_db.get_client_by_id(cid, db_path=self.db_name)
        self.assertEqual(updated_client["weight"], 63.5)

    def test_save_and_get_plans(self):
        cid = poweryoga_db.add_client("حمید", "کریمی", 32, 175.0, 78.0, "یوگا مبتدی", db_path=self.db_name)
        plan_id = poweryoga_db.save_plan(
            client_id=cid,
            plan_type="combined",
            title="برنامه هوشمند پاور یوگا",
            content="محتوای برنامه پاور یوگا...",
            db_path=self.db_name
        )
        self.assertIsNotNone(plan_id)

        plans = poweryoga_db.get_client_plans(cid, db_path=self.db_name)
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]["title"], "برنامه هوشمند پاور یوگا")

if __name__ == "__main__":
    unittest.main()
