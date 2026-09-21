import asyncio
from celery import Celery
from typing import List, Dict, Any, Optional
import json
import uuid
import redis.asyncio as redis

# Assume your FastAPI app's ai_assistant routes are in this module
# You may need to adjust the import path based on your project structure.
# from backend.blueprints.ai_assistant.routes import send_structured_ai_alert

# Assume the AI tool for calling Groq is here
from app.utils.ai_tools import call_groq_sync

# Configure Celery. Replace 'redis://localhost:6379/0' with your broker URL.
celery_app = Celery('tasks', broker='redis://localhost:6379/0')

# This would typically come from a shared config module
REDIS_URL = "redis://localhost:6379/0"

async def send_structured_ai_alert(
    org_id: int,
    user_id: str,
    message: str,
    alert_type: str,
    icon: Optional[str] = None,
    action_label: Optional[str] = None,
    action_url: Optional[str] = None,
):
    """Publishes a structured AI alert to the Redis 'ai-alerts' channel."""
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    icon_map = {"Insight": "⚡", "Update": "✅", "Security": "🔒", "Chat": "💬", "Error": "❗"}

    payload = {
        "id": str(uuid.uuid4()),
        "message": message,
        "timestamp": "now", # In a real app, use datetime.utcnow().isoformat()
        "type": alert_type,
        "icon": icon or icon_map.get(alert_type),
    }
    if action_label and action_url:
        payload["action"] = {"label": action_label, "url": action_url}

    message_to_publish = json.dumps({"org_id": org_id, "user_id": user_id, "payload": payload})
    await redis_client.publish("ai-alerts", message_to_publish)
    await redis_client.close()


@celery_app.task
def long_running_audit_task(org_id: int, user_id: str):
    """
    An example Celery task that performs a long-running operation
    and sends a proactive notification upon completion.
    """
    # --- Begin long-running process ---
    # e.g., process 14,000 records for a financial audit
    print(f"Starting audit for organization {org_id}...")
    processed_records = 14000
    # time.sleep(300) # Simulate a 5-minute task
    print(f"Audit complete for organization {org_id}.")
    # --- End long-running process ---

    # Send a proactive alert to the user via WebSocket.
    # Since this task runs in a synchronous Celery worker, we use
    # asyncio.run() to execute the async alert function.
    asyncio.run(send_structured_ai_alert(
        org_id=org_id,
        user_id=user_id,
        message=f"The cross-departmental financial audit is complete. I have processed {processed_records} records.",
        alert_type="Update",
        action_label="View Executive Summary",
        action_url=f"/reports/audits/financial-q2-2026"
    ))

    return {"status": "complete", "processed_records": processed_records}

@celery_app.task
def process_vani_chat(prompt_structure: List[Dict[str, Any]], org_id: int, user_id: str):
    """
    Asynchronous task to process a chat message with Vani, call the AI,
    and send the response back via WebSocket.
    """
    try:
        # 1. Call the AI model with the provided prompt structure
        response_text = call_groq_sync(prompt_structure)

        # 2. Send the response back to the specific user who made the request.
        #    This requires the WebSocket manager to handle user-specific connections.
        asyncio.run(send_structured_ai_alert(
            org_id=org_id,
            user_id=user_id, # Target the specific user
            message=response_text,
            alert_type="Chat",
        ))
        return {"status": "complete", "response": response_text}
    except Exception as e:
        # In case of an error, send an error message back to the user
        error_message = f"Sorry, I encountered an error: {str(e)}"
        asyncio.run(send_structured_ai_alert(
            org_id=org_id,
            user_id=user_id,
            message=error_message,
            alert_type="Error",
        ))
        return {"status": "failed", "error": str(e)}