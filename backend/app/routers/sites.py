from fastapi import APIRouter, Depends, Request

from ..auth import get_current_user
from ..models import Site, UserRecord


router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get("", response_model=list[Site], operation_id="getSites")
def list_sites(request: Request, user: UserRecord = Depends(get_current_user)) -> list[Site]:
    return request.app.state.store.list_sites(user)
