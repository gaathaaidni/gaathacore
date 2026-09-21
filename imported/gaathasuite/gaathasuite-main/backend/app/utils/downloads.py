from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.models.user import User
from app.utils.dependencies import get_current_user
from app.utils.signing import verify_token
import os


EXPORT_DIRECTORY = os.path.realpath(os.getenv("EXPORT_DIRECTORY", "/tmp"))

router = APIRouter(prefix="/download", tags=["Downloads"])

@router.get("/")
async def secure_file_download(
    token: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    """
    Serves files from the temporary export directory using a signed token.
    The signed payload must match the authenticated user and organization to prevent
    cross-tenant access via guessed or replayed download tokens.
    """
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Download link expired or invalid.")

    token_user_id = payload.get("user_id")
    token_org_id = payload.get("org_id")
    if token_user_id != current_user.id or token_org_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="You do not have access to this export.")

    file_path = payload.get("path")

    if not isinstance(file_path, str):
        raise HTTPException(status_code=404, detail="File not found.")

    resolved_path = os.path.realpath(file_path)
    if (
        os.path.dirname(resolved_path) != EXPORT_DIRECTORY
        or not os.path.basename(resolved_path).startswith("export_")
        or not os.path.isfile(resolved_path)
    ):
        raise HTTPException(status_code=404, detail="File not found.")

    filename = os.path.basename(resolved_path)
    return FileResponse(path=resolved_path, filename=filename)