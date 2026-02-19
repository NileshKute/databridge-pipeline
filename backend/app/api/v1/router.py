from fastapi import APIRouter

from backend.app.api.v1.endpoints import auth, shotgrid, transfers, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["Transfers"])
api_router.include_router(shotgrid.router, prefix="/shotgrid", tags=["ShotGrid"])
