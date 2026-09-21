from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.utils.dependencies import get_current_org_id, get_current_user_id
from typing import List, Optional, Dict
from pydantic import BaseModel

router = APIRouter(prefix="/import", tags=["Data Import"])

class CustomExportRequest(BaseModel):
    resource_type: str
    columns: List[str]
    filters: Optional[Dict] = None

@router.post("/{resource_type}")
async def upload_csv_for_import(
    resource_type: str,
    file: UploadFile = File(...),
    org_id: int = Depends(get_current_org_id),
    user_id: int = Depends(get_current_user_id)
):
    """
    Accepts a CSV file and triggers an asynchronous background import.
    Supported types: 'items', 'customers'.
    """
    if resource_type not in ["items", "customers"]:
        raise HTTPException(status_code=400, detail="Unsupported resource type")

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Read content and decode
    try:
        content = await file.read()
        decoded_content = content.decode('utf-8')
        from app.tasks.background_tasks import process_bulk_import

        process_bulk_import.delay(decoded_content, resource_type, org_id, user_id)
        return {"message": f"Import for {resource_type} started in the background."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@router.post("/export/{resource_type}")
async def trigger_data_export(
    resource_type: str,
    org_id: int = Depends(get_current_org_id),
    user_id: int = Depends(get_current_user_id)
):
    """
    Triggers an asynchronous background export of data to a CSV file.
    Supported types: 'items', 'invoices', 'customers'.
    """
    supported_types = ["items", "invoices", "customers"]
    if resource_type not in supported_types:
        raise HTTPException(status_code=400, detail=f"Unsupported resource type for export. Supported: {', '.join(supported_types)}")
    
    from app.tasks.background_tasks import export_data

    export_data.delay(resource_type, org_id, user_id)
    return {"message": f"Export for {resource_type} started in the background. You will be notified when it's ready."}

@router.post("/export/custom")
async def trigger_custom_export(
    request: CustomExportRequest,
    org_id: int = Depends(get_current_org_id),
    user_id: int = Depends(get_current_user_id)
):
    """
    Triggers a custom background export with specific columns and filters.
    """
    from app.tasks.background_tasks import export_data

    export_data.delay(
        request.resource_type, 
        org_id, 
        user_id, 
        columns=request.columns, 
        filters=request.filters
    )
    return {"message": "Custom export initiated. You will receive an in-app notification upon completion."}