import pandas as pd
from .base import BaseCSVImporter

class ChaseCSVImporter(BaseCSVImporter):
    def parse(self, filepath):
        df = pd.read_csv(filepath, on_bad_lines='warn')

        # Convert Amount to numeric
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df = df.dropna(subset=['Amount'])

        # Parse dates
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
        df['Post Date'] = pd.to_datetime(df['Post Date'], errors='coerce')

        df = df.dropna(subset=['Transaction Date'])

        transactions = []
        for _, row in df.iterrows():
            transactions.append((
                row['Transaction Date'].strftime('%Y-%m-%d'),
                row['Post Date'].strftime('%Y-%m-%d') if pd.notnull(row['Post Date']) else None,
                row['Description'],
                None,                     # no Original Description in chase CSV
                row.get('Category', None),
                row['Amount'],
                row.get('Type', None),
                None,                     # no Account column
                'chase',                  # source
                None,                     # no Tags
                row.get('Memo', None)
            ))
        return transactions

