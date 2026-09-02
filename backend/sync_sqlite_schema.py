import sqlite3
import asyncio
from app.db.session import engine, Base
import app.modules.iam.models
import app.modules.jobs.models
import app.modules.fleet.models
import app.modules.dashboard.models
import app.modules.notifications.models
import app.modules.audit.models
import app.modules.work.models
import app.modules.assets.models
import app.modules.requests.models
import app.modules.materials.models
import app.modules.contractors.models
import app.modules.sla.models
import app.modules.workflow.models

def sync_columns():
    conn = sqlite3.connect('test_dwrms.db')
    cursor = conn.cursor()

    for table_name, table in Base.metadata.tables.items():
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if not existing_cols:
            continue
        for col in table.columns:
            if col.name not in existing_cols:
                col_type = str(col.type)
                if any(t in col_type for t in ['VARCHAR', 'String', 'UUID', 'Text']):
                    sql_type = 'TEXT'
                elif any(t in col_type for t in ['INTEGER', 'Boolean', 'INT']):
                    sql_type = 'INTEGER'
                elif any(t in col_type for t in ['FLOAT', 'Float', 'Numeric']):
                    sql_type = 'REAL'
                elif any(t in col_type for t in ['DATETIME', 'DateTime', 'Date']):
                    sql_type = 'TIMESTAMP'
                else:
                    sql_type = 'TEXT'
                print(f"Adding missing column: {table_name}.{col.name} ({sql_type})")
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {sql_type}")
                except Exception as e:
                    print(f"Error adding {table_name}.{col.name}: {e}")

    conn.commit()
    conn.close()

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    sync_columns()
    asyncio.run(create_tables())
    print("Database schema synchronization complete!")
