import asyncio
from app.db.session import engine, Base
import app.modules.iam.models
import app.modules.jobs.models
import app.modules.jobs.report_models
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
import app.modules.approvals.models
import app.modules.common.models

async def init():
    async with engine.begin() as conn:
        print("Creating all tables in PostgreSQL...")
        await conn.run_sync(Base.metadata.create_all)
        print(f"[SUCCESS] Created {len(Base.metadata.tables)} tables in PostgreSQL database.")

if __name__ == "__main__":
    asyncio.run(init())
