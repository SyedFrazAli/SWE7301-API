import sqlite3

def migrate_db():
    try:
        conn = sqlite3.connect('run.db')
        cursor = conn.cursor()
        
        # Add columns if they don't exist
        columns = [
            ("is_verified", "INTEGER DEFAULT 0"),
            ("otp_code", "TEXT"),
            ("otp_created_at", "DATETIME")
        ]
        
        for col, dtype in columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
                print(f"Added column {col}")
            except sqlite3.OperationalError as e:
                print(f"Column {col} likely exists or error: {e}")
        
        conn.commit()
        conn.close()
        print("Migration complete.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_db()
