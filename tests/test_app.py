import os
import tempfile
import unittest

from campusbite import create_app


class CampusBiteFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir=os.path.dirname(__file__))
        self.database = os.path.join(self.temp_dir.name, "test.db")
        self.app = create_app({"TESTING": True, "DATABASE": self.database, "SECRET_KEY": "test-secret"})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def register_student(self):
        return self.client.post("/register", data={
            "full_name": "Aarav Sharma",
            "email": "aarav@college.edu",
            "student_id": "24CS1042",
            "password": "CampusPass123",
        }, follow_redirects=True)

    def login_admin(self):
        return self.client.post("/admin/login", data={
            "email": "admin@campusbite.local", "password": "CampusBite@2026",
        }, follow_redirects=True)

    def food_id(self, name="Veg Burger"):
        with self.app.app_context():
            from campusbite.db import get_db
            return get_db().execute("SELECT id FROM food_items WHERE name = ?", (name,)).fetchone()[0]

    def add_to_cart(self, food_id=None, times=1):
        food_id = food_id or self.food_id()
        for _ in range(times):
            response = self.client.post(f"/cart/add/{food_id}", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
        return food_id

    def test_registration_login_profile_and_menu_search(self):
        response = self.register_student()
        self.assertIn(b"Welcome to CampusBite", response.data)
        self.assertEqual(self.client.get("/profile").status_code, 200)
        response = self.client.get("/menu?q=burger&category=Fast+Food")
        self.assertIn(b"Veg Burger", response.data)
        self.assertIn(b"Chicken Burger", response.data)
        self.client.post("/logout")
        self.assertEqual(self.client.get("/profile", follow_redirects=True).status_code, 200)
        response = self.client.post("/login", data={"email": "aarav@college.edu", "password": "CampusPass123"}, follow_redirects=True)
        self.assertIn(b"Good to see you", response.data)

    def test_home_and_category_recommendations(self):
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertIn(b"Your break", home.data)
        self.assertIn(b"Today's crowd-pleasers", home.data)
        snacks = self.client.get("/menu?category=Snacks")
        self.assertIn(b"Popular in Snacks", snacks.data)
        self.assertIn(b"Quick picks from this category", snacks.data)

    def test_cart_quantity_remove_and_clear(self):
        self.register_student()
        food_id = self.add_to_cart(times=2)
        response = self.client.get("/cart")
        self.assertIn("₹80".encode(), response.data)
        self.client.post(f"/cart/update/{food_id}", data={"quantity": "3"})
        self.assertIn("₹120".encode(), self.client.get("/cart").data)
        self.client.post(f"/cart/remove/{food_id}")
        self.assertIn(b"Your bag is taking a break", self.client.get("/cart").data)
        self.add_to_cart()
        self.client.post("/cart/clear")
        self.assertIn(b"Your bag is taking a break", self.client.get("/cart").data)

    def test_cash_order_token_history_and_admin_tracking(self):
        self.register_student()
        self.add_to_cart(times=2)
        response = self.client.post("/checkout", data={"payment_method": "cash"})
        self.assertEqual(response.status_code, 302)
        token_url = response.headers["Location"]
        token_response = self.client.get(token_url)
        self.assertIn(b"ORDER CONFIRMED", token_response.data)
        self.assertIn(b"CB", token_response.data)
        with self.app.app_context():
            from campusbite.db import get_db
            order = get_db().execute("SELECT * FROM orders").fetchone()
            payment = get_db().execute("SELECT * FROM payments WHERE order_id = ?", (order["id"],)).fetchone()
            self.assertEqual(order["status"], "confirmed")
            self.assertEqual(order["payment_status"], "pending")
            self.assertEqual(payment["status"], "pending")
            order_id = order["id"]
        self.assertEqual(self.client.get("/orders").status_code, 200)
        self.assertEqual(self.client.get(f"/orders/{order_id}").status_code, 200)
        self.login_admin()
        self.client.post(f"/admin/orders/{order_id}/status", data={"status": "preparing"})
        self.client.post("/login", data={"email": "aarav@college.edu", "password": "CampusPass123"})
        tracked = self.client.get(f"/orders/{order_id}")
        self.assertIn(b"Preparing", tracked.data)

    def test_upi_demo_payment_simulation(self):
        self.register_student()
        self.add_to_cart()
        response = self.client.post("/checkout", data={"payment_method": "upi"})
        payment_url = response.headers["Location"]
        payment_page = self.client.get(payment_url)
        self.assertIn(b"visual demo only", payment_page.data)
        self.assertIn(b"No money is transferred", payment_page.data)
        self.client.post(payment_url)
        token_response = self.client.get(payment_url.replace("/payment/", "/token/"))
        self.assertIn(b"DEMO PAYMENT SUCCESSFUL", token_response.data)
        with self.app.app_context():
            from campusbite.db import get_db
            order = get_db().execute("SELECT * FROM orders").fetchone()
            payment = get_db().execute("SELECT * FROM payments WHERE order_id = ?", (order["id"],)).fetchone()
            self.assertEqual(order["payment_status"], "paid")
            self.assertEqual(payment["status"], "paid")
            self.assertTrue(payment["transaction_ref"].startswith("DEMO-"))

    def test_admin_food_availability_and_menu_edit(self):
        self.login_admin()
        food_id = self.food_id()
        response = self.client.get("/admin")
        self.assertIn(b"Menu management", response.data)
        self.client.post("/admin/foods", data={"action": "toggle", "food_id": food_id})
        self.assertIn(b"Sold out", self.client.get("/menu").data)
        self.client.post("/admin/foods", data={
            "action": "save", "food_id": food_id, "name": "Veg Burger", "description": "Updated description",
            "category": "Fast Food", "price": "45", "image_url": "",
        })
        self.assertIn(b"Updated description", self.client.get("/menu").data)
        self.client.post("/admin/foods", data={
            "action": "save", "name": "Masala Dosa", "description": "Crispy dosa", "category": "Breakfast", "price": "55",
        })
        self.assertIn(b"Masala Dosa", self.client.get("/menu").data)
        with self.app.app_context():
            from campusbite.db import get_db
            dosa_id = get_db().execute("SELECT id FROM food_items WHERE name = 'Masala Dosa'").fetchone()[0]
        self.client.post("/admin/foods", data={"action": "delete", "food_id": str(dosa_id)})
        self.assertNotIn(b"Masala Dosa", self.client.get("/menu").data)

    def test_feedback_submission_and_admin_view(self):
        self.register_student()
        food_id = self.food_id()
        response = self.client.post("/feedback", data={
            "rating": "4", "feedback_type": "suggestion", "food_id": str(food_id), "comment": "Please add more mint chutney.",
        }, follow_redirects=True)
        self.assertIn(b"Thanks! Your feedback", response.data)
        self.login_admin()
        self.assertIn(b"Please add more mint chutney", self.client.get("/admin").data)

    def test_auth_guards_guest_cart_and_availability(self):
        response = self.client.get("/checkout", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])
        food_id = self.add_to_cart()
        self.register_student()
        self.assertIn(b"Veg Burger", self.client.get("/cart").data)
        self.login_admin()
        self.client.post("/admin/foods", data={"action": "toggle", "food_id": food_id})
        self.client.post("/logout")
        self.assertIn(b"Sold out", self.client.get("/menu").data)

    def test_csrf_blocks_unprotected_form_posts(self):
        with tempfile.TemporaryDirectory(dir=os.path.dirname(__file__)) as test_dir:
            protected_app = create_app({
                "TESTING": False,
                "DATABASE": os.path.join(test_dir, "csrf.db"),
                "SECRET_KEY": "csrf-test-secret",
            })
            client = protected_app.test_client()
            self.assertEqual(client.post("/register", data={"email": "test@college.edu"}).status_code, 400)
            client.get("/register")
            with client.session_transaction() as session:
                token = session["csrf_token"]
            self.assertEqual(client.post("/register", data={
                "csrf_token": token,
                "full_name": "Test Student",
                "email": "test@college.edu",
                "student_id": "TEST-01",
                "password": "TestPass123",
            }).status_code, 302)


if __name__ == "__main__":
    unittest.main()
