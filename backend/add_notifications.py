import asyncio
import sqlite3

def setup_db():
    conn = sqlite3.connect("jobcard.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notification_rules (
        id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 0,
        escalation_delay_hours INTEGER,
        escalation_role TEXT,
        message_template TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id),
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 0,
        is_read BOOLEAN NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escalation_timers (
        id TEXT PRIMARY KEY,
        resource_type TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        due_at DATETIME NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print("Notification tables created successfully.")

if __name__ == "__main__":
    setup_db()
