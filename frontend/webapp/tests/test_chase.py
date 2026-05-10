import unittest
import pandas as pd
import tempfile
import os
from importers.chase import ChaseCSVImporter

class TestChaseCSVImporter(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv')
        self.temp_file.write('Transaction Date,Post Date,Amount,Description,Category,Type,Memo\n')
        self.temp_file.write('2023-02-01,2023-02-02,150.00,Amazon,Shopping,Credit,\n')
        self.temp_file.write('2023-02-03,2023-02-04,-50.00,Refund,Returns,Debit,\n')
        self.temp_file.write('notadate,2023-02-05,100.00,InvalidDate,Other,Credit,\n')  # Invalid date
        self.temp_file.write('2023-02-06,2023-02-07,abc,InvalidAmount,Other,Credit,\n')  # Invalid amount
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_parse_valid_and_invalid_rows(self):
        importer = ChaseCSVImporter()
        transactions = importer.parse(self.temp_file.name)
        # Only valid rows should be parsed (invalid amount and date dropped)
        self.assertEqual(len(transactions), 2)
        # First transaction date
        self.assertEqual(transactions[0][0], '2023-02-01')
        # Second transaction date
        self.assertEqual(transactions[1][0], '2023-02-03')
        # Amounts
        self.assertEqual(transactions[0][5], 150.00)
        self.assertEqual(transactions[1][5], -50.00)
        # Description
        self.assertEqual(transactions[0][2], 'Amazon')
        self.assertEqual(transactions[1][2], 'Refund')

if __name__ == '__main__':
    unittest.main()
