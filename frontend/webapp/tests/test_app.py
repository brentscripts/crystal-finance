import unittest
from webapp.app import app

class TestAppRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Transactions', response.data)

    def test_dashboard_route(self):
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)

    def test_add_route_get(self):
        response = self.client.get('/add')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add', response.data)

    def test_api_expenses_by_category(self):
        response = self.client.get('/api/expenses_by_category')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_api_monthly_cash_flow(self):
        response = self.client.get('/api/monthly_cash_flow')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_api_income_vs_expenses(self):
        response = self.client.get('/api/income_vs_expenses')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_api_donations_vs_income(self):
        response = self.client.get('/api/donations_vs_income')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

if __name__ == '__main__':
    unittest.main()
