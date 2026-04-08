import sqlite3
import os

db_path = os.path.expanduser('~/.devready/state.db')
if not os.path.exists(db_path):
    print("DB does not exist yet.")
    exit(0)

conn = sqlite3.connect(db_path)
try:
    # SQLModel JSON column usually maps to TEXT in SQLite
    conn.execute('ALTER TABLE environmentsnapshot ADD COLUMN violations TEXT')
    conn.commit()
    print("Successfully added 'violations' column.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("Column already exists.")
    else:
        print(f"Error: {e}")
finally:
    conn.close()
