import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.modules.approvals.models import WorkflowDefinition, WorkflowStepDef
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with async_session() as session:
        # Emergency Workflow
        w1 = WorkflowDefinition(
            id=uuid.uuid4(),
            name="Emergency Response",
            description="Emergency workflow requiring only supervisor approval",
            workflow_type="EMERGENCY",
            priority=100
        )
        w1_s1 = WorkflowStepDef(id=uuid.uuid4(), workflow_id=w1.id, step_number=1, authority_role="SUPERVISOR", required_permission="job_card:approve")
        
        # High Risk / HSE Critical
        w2 = WorkflowDefinition(
            id=uuid.uuid4(),
            name="High Risk / HSE",
            description="Requires Supervisor and HSE",
            risk_level="HIGH",
            priority=90
        )
        w2_s1 = WorkflowStepDef(id=uuid.uuid4(), workflow_id=w2.id, step_number=1, authority_role="SUPERVISOR", required_permission="job_card:approve")
        w2_s2 = WorkflowStepDef(id=uuid.uuid4(), workflow_id=w2.id, step_number=2, authority_role="HSE", required_permission="approval:hse_approve")
        
        # Machine Requisition > 50k
        w3 = WorkflowDefinition(
            id=uuid.uuid4(),
            name="Expensive Machine Requisition",
            description="Machine requisitions over 50k",
            resource_type="machine_requisition",
            min_cost=50000.0,
            priority=80
        )
        w3_s1 = WorkflowStepDef(id=uuid.uuid4(), workflow_id=w3.id, step_number=1, authority_role="RESOURCE_CONTROLLER", required_permission="machine_requisition:approve")
        w3_s2 = WorkflowStepDef(id=uuid.uuid4(), workflow_id=w3.id, step_number=2, authority_role="DEPT_MANAGER", required_permission="job_card:approve")
        w3_s3 = WorkflowStepDef(id=uuid.uuid4(), workflow_id=w3.id, step_number=3, authority_role="FINANCE", required_permission="approval:finance_approve")

        # Standard Default
        w4 = WorkflowDefinition(
            id=uuid.uuid4(),
            name="Standard Approval",
            description="Default fallback approval",
            priority=0
        )
        w4_s1 = WorkflowStepDef(id=uuid.uuid4(), workflow_id=w4.id, step_number=1, authority_role="SUPERVISOR", required_permission="job_card:approve")

        session.add_all([w1, w1_s1, w2, w2_s1, w2_s2, w3, w3_s1, w3_s2, w3_s3, w4, w4_s1])
        await session.commit()
        print("Seeded workflows")

if __name__ == "__main__":
    asyncio.run(seed())
