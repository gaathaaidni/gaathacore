from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Optional
import json
import redis.asyncio as redis
import asyncio

from app.utils.dependencies import get_db, get_current_org_id, get_current_user, get_current_user_ws
from . import models, schemas
from .tasks import process_vani_chat
from app.utils.ai_tools import GROQ_API_KEY, get_vani_system_prompt

hr_router = APIRouter(
    prefix="/api/v2/hr",
    tags=["HR"],
)

ai_router = APIRouter(
    prefix="/ai-assistant",
    tags=["AI Assistant"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    task_id: str
    status: str

class HealthResponse(BaseModel):
    status: str
    name: str
    version: str
    groq_available: bool


class ConnectionManager:
    """
    Manages active WebSocket connections and broadcasts messages received
    from a Redis Pub/Sub channel.
    """
    def __init__(self):
        # Structure: {org_id: {user_id: WebSocket}}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: int, user_id: str):
        await websocket.accept()
        if org_id not in self.active_connections:
            self.active_connections[org_id] = {}
        self.active_connections[org_id][user_id] = websocket

    def disconnect(self, org_id: int, user_id: str):
        if org_id in self.active_connections and user_id in self.active_connections[org_id]:
            del self.active_connections[org_id][user_id]
            if not self.active_connections[org_id]:
                del self.active_connections[org_id]

    async def _send_to_user(self, org_id: int, user_id: str, message: str):
        if org_id in self.active_connections and user_id in self.active_connections[org_id]:
            try:
                await self.active_connections[org_id][user_id].send_text(message)
            except WebSocketDisconnect:
                self.disconnect(org_id, user_id)

    async def broadcast_from_redis(self, message_data: str):
        """Parses a message from Redis and sends it to the correct user."""
        try:
            data = json.loads(message_data)
            org_id = data.get("org_id")
            user_id = data.get("user_id")
            payload = data.get("payload")

            if org_id is not None and user_id is not None and payload is not None:
                await self._send_to_user(int(org_id), str(user_id), json.dumps(payload))
        except (json.JSONDecodeError, TypeError):
            # Ignore malformed messages
            pass

manager = ConnectionManager()

async def redis_pubsub_listener(redis_client: redis.Redis):
    """Listens to the 'ai-alerts' channel and broadcasts messages."""
    async with redis_client.pubsub() as pubsub:
        await pubsub.subscribe("ai-alerts")
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message and "data" in message:
                await manager.broadcast_from_redis(message["data"])

@hr_router.websocket("/ws/{org_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    org_id: int,
    user: models.User = Depends(get_current_user_ws),
):
    user_id = str(user.id)
    await manager.connect(websocket, org_id, user_id)
    try:
        while True:
            # Keep connection alive and handle potential client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(org_id, user_id)


@hr_router.get("/employees", response_model=List[schemas.Employee])
async def list_employees(
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve a list of employees for the current organization.
    """
    stmt = select(models.Employee).where(models.Employee.organization_id == org_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    employees = result.scalars().all()
    return employees


@hr_router.post("/employees", response_model=schemas.Employee, status_code=201)
async def create_employee(
    employee_in: schemas.EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create a new employee for the current organization.
    """
    db_employee = models.Employee(**employee_in.dict(), organization_id=current_user.organization_id)
    db.add(db_employee)
    try:
        await db.commit()
        await db.refresh(db_employee)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An employee with this email already exists in your organization.",
        )
    return db_employee


@hr_router.get("/employees/{employee_id}", response_model=schemas.Employee)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
):
    """
    Retrieve a specific employee by their ID, scoped to the current organization.
    """
    stmt = select(models.Employee).where(
        models.Employee.id == employee_id, models.Employee.organization_id == org_id
    )
    employee = (await db.execute(stmt)).scalar_one_or_none()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@hr_router.put("/employees/{employee_id}", response_model=schemas.Employee)
async def update_employee(
    employee_id: int,
    employee_in: schemas.EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
):
    """
    Update an employee's details.
    """
    stmt = select(models.Employee).where(
        models.Employee.id == employee_id, models.Employee.organization_id == org_id
    )
    result = await db.execute(stmt)
    db_employee = result.scalar_one_or_none()

    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = employee_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_employee, key, value)

    db.add(db_employee)
    await db.commit()
    await db.refresh(db_employee)
    return db_employee


@hr_router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
):
    """
    Delete an employee.
    """
    stmt = select(models.Employee).where(
        models.Employee.id == employee_id, models.Employee.organization_id == org_id
    )
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    await db.delete(employee)
    await db.commit()


@ai_router.post("/chat", response_model=ChatResponse, status_code=202)
async def chat(
    chat_request: ChatRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Handle chat messages from the Vani widget."""
    user_message = chat_request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    if not GROQ_API_KEY:
        # In an async context, we can't easily return a sync response and also
        # send a websocket message. For now, we'll raise an error.
        # A more advanced implementation could send a websocket message back.
        raise HTTPException(status_code=503, detail="AI assistant is not configured.")

    prompt_structure = [
        {"role": "system", "content": get_vani_system_prompt()},
        {"role": "user", "content": user_message},
    ]

    task = process_vani_chat.delay(
        prompt_structure=prompt_structure,
        org_id=current_user.organization_id,
        user_id=str(current_user.id)
    )

    return {"task_id": task.id, "status": "Processing..."}


@ai_router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint for Vani."""
    groq_available = bool(GROQ_API_KEY)
    return {
        "status": "online",
        "name": "Vani",
        "version": "1.0.0",
        "groq_available": groq_available,
    }