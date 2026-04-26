import pandas as pd

class BaseCSVImporter:
    def parse(self, filepath):
        """
        Reads CSV file into pandas DataFrame.
        Subclasses should override this to implement custom parsing and return
        a list of tuples representing transactions ready for DB insert.
        """
        df = pd.read_csv(filepath, on_bad_lines='warn')
        return df

