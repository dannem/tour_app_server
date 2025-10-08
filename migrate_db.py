import sqlite3


def migrate_database():
    conn = sqlite3.connect("tour_app.db")
    cursor = conn.cursor()

    # Check if the name column exists
    cursor.execute("PRAGMA table_info(waypoints)")
    columns = [column[1] for column in cursor.fetchall()]

    if "name" not in columns:
        print("Adding 'name' column to waypoints table...")
        cursor.execute("ALTER TABLE waypoints ADD COLUMN name TEXT")
        conn.commit()
        print("Migration successful!")
    else:
        print("'name' column already exists. No migration needed.")

    conn.close()


if __name__ == "__main__":
    migrate_database()
