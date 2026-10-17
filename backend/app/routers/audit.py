from fastapi import APIRouter, Depends, Request

from ..auth import require_roles
from ..models import AuditEvent, Role, UserRecord


router = APIRouter(prefix="/audit-events", tags=["Audit"])


@router.get("", response_model=list[AuditEvent], operation_id="getAuditEvents")
def list_audit_events(
    request: Request,
    user: UserRecord = Depends(require_roles(Role.ADMIN, Role.APPROVER)),
) -> list[AuditEvent]:
    return request.app.state.store.list_audit(user)
