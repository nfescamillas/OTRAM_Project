from fastapi import APIRouter, Depends, Query, Request, Response, status

from ..auth import get_current_user, require_roles
from ..models import Asset, AssetInput, AssetType, LifecycleState, Role, UserRecord


router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=list[Asset], operation_id="listAssets")
def list_assets(
    request: Request,
    search: str | None = Query(default=None, max_length=160),
    siteId: str | None = None,
    type: AssetType | None = None,
    lifecycle: LifecycleState | None = None,
    user: UserRecord = Depends(get_current_user),
) -> list[Asset]:
    return request.app.state.store.list_assets(
        user, search=search, site_id=siteId, asset_type=type, lifecycle=lifecycle
    )


@router.post("", response_model=Asset, status_code=status.HTTP_201_CREATED, operation_id="createAsset")
def create_asset(
    payload: AssetInput,
    request: Request,
    user: UserRecord = Depends(require_roles(Role.ADMIN, Role.ASSESSOR)),
) -> Asset:
    return request.app.state.store.create_asset(user, payload)


@router.get("/export.csv", operation_id="exportAssetsCsv")
def export_assets(
    request: Request,
    search: str | None = Query(default=None, max_length=160),
    siteId: str | None = None,
    type: AssetType | None = None,
    lifecycle: LifecycleState | None = None,
    user: UserRecord = Depends(require_roles(Role.ADMIN, Role.ASSESSOR, Role.APPROVER)),
) -> Response:
    content = request.app.state.store.export_assets(
        user, search=search, site_id=siteId, asset_type=type, lifecycle=lifecycle
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="otarm-assets.csv"'},
    )


@router.get("/{assetId}", response_model=Asset, operation_id="getAsset")
def get_asset(assetId: str, request: Request,
              user: UserRecord = Depends(get_current_user)) -> Asset:
    return request.app.state.store.get_asset(user, assetId)
