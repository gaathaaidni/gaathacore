from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import random

# Assuming you have a dependency injection system for authentication
# from app.utils.dependencies import get_current_org_id
# Assuming your Celery app and tasks are defined here
from backend.blueprints.ai_assistant.tasks import long_running_audit_task, celery_app

# --- Pydantic Models ---

class FinancialBriefRequest(BaseModel):
    """Defines the request model for Vani's financial brief tool."""
    time_period: str
    focus_areas: List[str]
    comparison_period: Optional[str] = None


class FinancialBriefResponse(BaseModel):
    """Defines the response model for the financial brief tool."""
    time_period: str
    total_revenue: float
    total_expenses: float
    net_profit: float
    profit_margin: float
    key_insights: List[str]

class AuditRequest(BaseModel):
    """Defines the request model for Vani's audit initiation tool."""
    audit_type: str = Field(..., description="The type of audit to perform, e.g., 'security_permissions'.")
    target_department_id: str = Field(..., description="The ID of the department to audit.")
    time_period_days: int = Field(..., gt=0, description="The number of days to look back for the audit.")


class AuditResponse(BaseModel):
    """Defines the response model for the audit initiation tool."""
    confirmation_message: str
    project_id: str
    tasks_created: int

class WorkspaceRequest(BaseModel):
    """Defines the request model for Vani's workspace provisioning tool."""
    workspace_template: str = Field(..., description="The template to use for the new workspace, e.g., 'quarterly-marketing-campaign'.")
    project_name: str = Field(..., description="The name for the new project.")
    budget_allocation: float = Field(..., gt=0, description="The budget to allocate in Gaatha Books.")
    lead_employee_id: str = Field(..., description="The ID of the employee to assign as the project lead.")


class WorkspaceResponse(BaseModel):
    """Defines the response model for the workspace provisioning tool."""
    confirmation_message: str
    project_id: str
    budget_allocated: float
    lead_employee_id: str

class AuditTaskResponse(BaseModel):
    """Defines the response for initiating a background audit task."""
    task_id: str
    status: str


tools_router = APIRouter(
    prefix="/api/v2/ai/tools",
    tags=["AI Tools"],
)


def _process_financial_brief(org_id: str, request: FinancialBriefRequest):
    """Placeholder for the actual data aggregation logic."""
    # In a real application, this function would:
    # 1. Connect to the database (e.g., Gaatha Books module).
    # 2. Run complex queries to aggregate revenue and expenses for the given time periods.
    # 3. Perform analysis to derive insights.
    # This can take time, which is why it's suitable for a background task.
    print(f"Processing financial brief for org {org_id} and period {request.time_period}...")


@tools_router.post("/generate-financial-brief", response_model=FinancialBriefResponse)
async def generate_financial_brief(
    request: FinancialBriefRequest,
    background_tasks: BackgroundTasks,
    # org_id: str = Depends(get_current_org_id) # Example of getting org context
):
    """
    An endpoint for Vani to generate a financial brief by aggregating data
    from multiple sources.
    """
    # background_tasks.add_task(_process_financial_brief, org_id, request)

    # For now, we return mock data immediately.
    revenue = random.uniform(500000, 2000000)
    expenses = random.uniform(200000, revenue * 0.8)
    net = revenue - expenses
    margin = (net / revenue) * 100 if revenue > 0 else 0

    return FinancialBriefResponse(
        time_period=request.time_period,
        total_revenue=round(revenue, 2),
        total_expenses=round(expenses, 2),
        net_profit=round(net, 2),
        profit_margin=round(margin, 2),
        key_insights=[
            "Cloud resource allocation saw a 15% increase, correlating with new client onboarding.",
            "Expense reports from the marketing department are 10% above the quarterly budget.",
        ],
    )

@tools_router.post("/initiate-audit", response_model=AuditResponse)
async def initiate_audit(
    request: AuditRequest,
    background_tasks: BackgroundTasks,
    # org_id: str = Depends(get_current_org_id) # Example of getting org context
):
    """
    An endpoint for Vani to initiate a cross-departmental audit.
    """
    # In a real application, this would be a background task.
    # background_tasks.add_task(_process_audit_initiation, org_id, request)

    # --- Placeholder Business Logic ---
    # 1. Query Gaatha HR for new employees in the department within the time period.
    num_employees_found = random.randint(3, 10)

    # 2. Create a new project in Gaatha Projects.
    new_project_id = f"audit-proj-{random.randint(1000, 9999)}"

    # 3. For each employee, generate tasks to review permissions.
    tasks_created = num_employees_found
    # --- End Placeholder ---

    confirmation_message = f"I have initiated the '{request.audit_type}' audit. A new project has been created, and {tasks_created} review tasks have been assigned."

    return AuditResponse(
        confirmation_message=confirmation_message, project_id=new_project_id, tasks_created=tasks_created
    )

@tools_router.post("/provision-workspace", response_model=WorkspaceResponse)
async def provision_workspace(
    request: WorkspaceRequest,
    background_tasks: BackgroundTasks,
    # org_id: str = Depends(get_current_org_id) # Example of getting org context
):
    """
    An endpoint for Vani to provision a new project workspace across multiple modules.
    """
    # --- Placeholder Business Logic ---
    # In a real application, this would be a background task that:
    # 1. Creates a new project in Gaatha Projects from a template.
    new_project_id = f"proj-{random.randint(1000, 9999)}"
    # 2. Allocates the budget in Gaatha Books and associates it with the project.
    budget_allocated = request.budget_allocation
    # 3. Assigns the lead employee in Gaatha HR.
    lead_employee_id = request.lead_employee_id
    # --- End Placeholder ---

    confirmation_message = (
        f"I have provisioned the new workspace '{request.project_name}'. "
        f"Project ID {new_project_id} has been created, a budget of {budget_allocated} has been allocated, "
        f"and {lead_employee_id} is now the project lead."
    )

    return WorkspaceResponse(
        confirmation_message=confirmation_message, project_id=new_project_id, budget_allocated=budget_allocated, lead_employee_id=lead_employee_id
    )

@tools_router.post("/trigger-long-audit", response_model=AuditTaskResponse)
async def trigger_long_audit(
    # In a real app, you would get the current user's ID from an auth dependency
    # current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """
    Triggers the long-running audit task in the background using Celery.
    """
    # This is the core of triggering the task.
    # .delay() sends the task to the Celery worker queue and returns immediately.
    # You would pass the necessary arguments to your task function here.
    user_id_placeholder = "user-123" # Replace with actual user ID from auth
    task = long_running_audit_task.delay(org_id=org_id, user_id=user_id_placeholder)

    # Return the task ID to the client.
    # The client can use this ID to poll for the task's status and result.
    return {"task_id": task.id, "status": "Task has been submitted."}

@tools_router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Poll for the status of a Celery background task.
    """
    task_result = celery_app.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
    }
    if task_result.status == "FAILURE":
        # Optionally include error information
        response["result"] = str(task_result.info)

    return response