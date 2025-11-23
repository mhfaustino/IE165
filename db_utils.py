import sqlite3
import pandas as pd
import os

# Path to database
DB_PATH = os.path.join(os.path.dirname(__file__), 'assets/inventory.db')

# List your CSV files and table names here
CSV_FILES = [
    os.path.join(os.path.dirname(__file__), 'assets/db/Date_Dimension.csv'),
    os.path.join(os.path.dirname(__file__), 'assets/db/Item_Dimension.csv'),
    os.path.join(os.path.dirname(__file__), 'assets/db/Job_Request_Fact_Table.csv'),
    os.path.join(os.path.dirname(__file__), 'assets/db/Section_Dimension.csv'),
]
TABLE_NAMES = ['Date_Dimension', 'Item_Dimension', 'Job_Request_Fact_Table', 'Section_Dimension']

def get_db_connection(db_path=DB_PATH):
    """Return a new SQLite connection."""
    return sqlite3.connect(db_path)

def import_csvs_to_sqlite(db_path=DB_PATH, csv_files=CSV_FILES, table_names=TABLE_NAMES):
    """Import CSV files into SQLite tables."""
    conn = sqlite3.connect(db_path)
    for csv_file, table_name in zip(csv_files, table_names):
        df = pd.read_csv(csv_file)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
