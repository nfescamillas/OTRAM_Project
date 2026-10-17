from fastapi import APIRouter, Depends, Request

from ..auth import get_current_user, require_roles
from ..models import RemediationAction, Role, UpdateActionStatusInput, UserRecord


router = APIRouter(tags=["Remediation"])


@router.get("/remediation", response_model=list[RemediationAction], operation_id="listRemediation")
def list_remediation(request: Request,
                     user: UserRecord = Depends(get_current_user)) -> list[RemediationAction]:
    return request.app.state.store.list_actions(user)


@router.patch("/actions/{actionId}/status", response_model=RemediationAction, operation_id="updateActionStatus")
def update_action_status(
    actionId: str,
    payload: UpdateActionStatusInput,
    request: Request,
    user: UserRecord = Depends(require_roles(Role.ADMIN, Role.ASSESSOR, Role.APPROVER)),
) -> RemediationAction:
    return request.app.state.store.update_action(user, actionId, payload.status)
