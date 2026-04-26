import pandas as pd
from .base import BaseCSVImporter

class BankCSVImporter(BaseCSVImporter):
    def parse(self, filepath):
        df = pd.read_csv(filepath, on_bad_lines='warn')

        # Clean and transform data
        # Convert 'Amount' to numeric, coercing invalids to NaN
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        # Make Amount negative for debits
        df.loc[df['Type'].str.lower() == 'debit', 'Amount'] *= -1
        # Drop rows where Amount is NaN (invalid or missing)
        df = df.dropna(subset=['Amount'])

        # Optionally parse 'Date' column to datetime, errors coerced to NaT
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        transactions = []
        for _, row in df.iterrows():
            transactions.append((
                row['Date'].strftime('%Y-%m-%d'),       # date as string YYYY-MM-DD
                None,                                   # post_date (not in bank CSV)
                row['Description'],
                row.get('Original Description', None),
                row.get('Category', None),
                row['Amount'],
                row.get('Type', None),
                row.get('Account', None),
                'bank',                                # source
                row.get('Tags', None),
                row.get('Memo', None)
            ))
        return transactions

