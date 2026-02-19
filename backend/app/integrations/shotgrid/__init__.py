from backend.app.core.config import settings
from backend.app.integrations.shotgrid.sg_client import ShotGridClient, sg_client
from backend.app.integrations.shotgrid.sg_fallback import MockShotGridClient, mock_sg_client

if settings.SHOTGRID_ENABLED and sg_client is not None:
    shotgrid_client = sg_client
else:
    shotgrid_client = mock_sg_client

__all__ = [
    "ShotGridClient",
    "sg_client",
    "MockShotGridClient",
    "mock_sg_client",
    "shotgrid_client",
]
