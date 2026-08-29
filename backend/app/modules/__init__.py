# modules package
from app.db.session import Base

# IAM models
from app.modules.iam.models import Department, User, Role, Permission, RolePermission, UserRole

# Jobs models
from app.modules.jobs.models import JobCard, JobCardAttachment, JobCardComment, JobCardActionLog

# Fleet models
from app.modules.fleet.models import MachineType, Machine, MachineRequisition, MachineReservation

# Common models
from app.modules.common.models import SMSMessage
