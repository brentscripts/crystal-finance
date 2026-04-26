import unittest
import pandas as pd
import tempfile
import os
from importers.bank import BankCSVImporter

class TestBankCSVImporter(unittest.TestCase):
    def setUp(self):
        # Create a temporary CSV file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv')
        self.temp_file.write('Date,Type,Amount,Description,Original Description,Category,Account,Tags,Memo\n')
        self.temp_file.write('2023-01-01,Debit,100.00,Groceries,,Food,Checking,,\n')
        self.temp_file.write('2023-01-02,Credit,200.00,Salary,,Income,Checking,,\n')
        self.temp_file.write('2023-01-03,Debit,abc,InvalidAmount,,Misc,Checking,,\n')  # Invalid amount
        self.temp_file.write('notadate,Debit,50.00,InvalidDate,,Misc,Checking,,\n')   # Invalid date
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_parse_valid_and_invalid_rows(self):
        importer = BankCSVImporter()
        transactions = importer.parse(self.temp_file.name)
        # Only valid rows should be parsed (invalid amount and date dropped)
        self.assertEqual(len(transactions), 2)
        # Debit should be negative
        self.assertEqual(transactions[0][5], -100.00)
        # Credit should be positive
        self.assertEqual(transactions[1][5], 200.00)
        # Date format
        self.assertEqual(transactions[0][0], '2023-01-01')
        self.assertEqual(transactions[1][0], '2023-01-02')
        # Description
        self.assertEqual(transactions[0][2], 'Groceries')
        self.assertEqual(transactions[1][2], 'Salary')

if __name__ == '__main__':
    unittest.main()
