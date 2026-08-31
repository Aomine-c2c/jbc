# modules package
from app.db.session import Base

# IAM & Location models
from app.modules.iam.models import Organization, Site, Location, Department, Section, Team, Position, User, Role, Permission, RolePermission, UserRole

# Jobs models
from app.modules.jobs.models import JobCard, JobCardAttachment, JobCardComment, JobCardActionLog

# Job Reports models
from app.modules.jobs.report_models import JobReport, JobReportProgressUpdate, JobReportMaterial, JobReportAttachment, JobReportAmendment

# Fleet models
from app.modules.fleet.models import MachineType, Machine, MachineRequisition, MachineReservation, RequisitionActionLog

# Approvals models
from app.modules.approvals.models import ApprovalRequest, ApprovalStep, WorkflowDefinition, WorkflowStepDef

# Audit models
from app.modules.audit.models import BusinessAuditLog

# Notifications models
from app.modules.notifications.models import Notification, NotificationRule, EscalationTimer

# Common models
from app.modules.common.models import SMSMessage

# Unified Work Management models
from app.modules.work.models import WorkItem, WorkItemActionLog, WorkItemAttachment, WorkItemComment, WorkItemPart

# Asset and Equipment Management models
from app.modules.assets.models import Asset, AssetActivityLog, AssetMaintenanceRecord, AssetAttachment

# Universal Request and Requisition models
from app.modules.requests.models import OperationalRequest, RequestMaterialItem, RequestActionLog, RequestComment, RequestAttachment

# Materials and Operational Inventory models
from app.modules.materials.models import MaterialCatalogItem, MaterialRequirement, MaterialTransaction

# Contractor and External Workforce models
from app.modules.contractors.models import (
    ContractorCompany,
    ContractorWorker,
    ContractorAssignment,
    ContractorWorkerAssignment,
    ContractorDocument,
)
