from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    activity,
    approvals,
    auth,
    notifications,
    scanning,
    shotgrid,
    transfer_ops,
    transfers,
    users,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["Transfers"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
api_router.include_router(scanning.router, prefix="/scanning", tags=["Data Team"])
api_router.include_router(transfer_ops.router, prefix="/transfer-ops", tags=["IT Team"])
api_router.include_router(shotgrid.router, prefix="/shotgrid", tags=["ShotGrid"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(activity.router, prefix="/activity", tags=["Activity Log"])
