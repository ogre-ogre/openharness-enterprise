"""
OpenHarness Enterprise - A2A Protocol Routes

FastAPI routes for A2A protocol endpoints.
"""

from __future__ import annotations

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Header
from fastapi.responses import StreamingResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from openharness.enterprise.a2a import (
    A2AService,
    get_a2a_service,
    SendMessageRequest,
    SendMessageResponse,
    StreamResponse,
    ListTasksRequest,
    ListTasksResponse,
    GetTaskRequest,
    CancelTaskRequest,
    TaskState,
    A2AError,
)
from openharness.enterprise.auth.middleware import get_current_user
from openharness.enterprise.storage.database import User


# Create router
router = APIRouter(prefix="/a2a", tags=["A2A Protocol"])


# ============================================================================
# Helper Functions
# ============================================================================

def get_base_url(request: Request) -> str:
    """Get base URL from request."""
    return str(request.base_url).rstrip("/")


def a2a_error(code: str, message: str, status_code: int = 400) -> JSONResponse:
    """Create A2A error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message
        }
    )


# ============================================================================
# Agent Card
# ============================================================================

@router.get("/agent-card")
@router.get("/.well-known/agent-card")
async def get_agent_card(request: Request):
    """
    Get the Agent Card.
    
    Returns agent capabilities, skills, and connection information.
    This endpoint is public (no authentication required) for discovery.
    """
    service = get_a2a_service()
    base_url = get_base_url(request)
    card = service.get_agent_card(base_url)
    
    return card.dict()


@router.get("/agent-card/extended")
async def get_extended_agent_card(
    request: Request,
    user: User = Depends(get_current_user)
):
    """
    Get the extended Agent Card (requires authentication).
    
    Returns additional details not available in the public card.
    """
    service = get_a2a_service()
    base_url = get_base_url(request)
    card = service.get_agent_card(base_url)
    
    # Add extended information
    card_dict = card.dict()
    card_dict["extended_info"] = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "permissions": ["all"] if user.role == "admin" else ["read", "write"]
    }
    
    return card_dict


# ============================================================================
# Send Message
# ============================================================================

@router.post("/message/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    req: Request,
    user: User = Depends(get_current_user)
):
    """
    Send a message to the agent.
    
    Creates a new task and returns the result when complete.
    Use streaming endpoint for real-time updates.
    """
    service = get_a2a_service()
    base_url = get_base_url(req)
    
    response = await service.send_message(request, user.id, base_url)
    return response


@router.post("/message/stream")
async def send_streaming_message(
    request: SendMessageRequest,
    req: Request,
    user: User = Depends(get_current_user)
):
    """
    Send a message and stream the response.
    
    Returns Server-Sent Events (SSE) with task updates.
    """
    service = get_a2a_service()
    base_url = get_base_url(req)
    
    async def event_generator():
        try:
            async for response in service.send_streaming_message(request, user.id, base_url):
                # SSE format
                data = response.dict(exclude_none=True)
                yield {
                    "event": "message",
                    "data": json.dumps(data, ensure_ascii=False)
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"code": "internal_error", "message": str(e)})
            }
    
    return EventSourceResponse(event_generator())


# ============================================================================
# Task Management
# ============================================================================

@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    history_length: Optional[int] = Query(None, description="Max history messages to return"),
    user: User = Depends(get_current_user)
):
    """
    Get task by ID.
    
    Returns the current state of a task including status and artifacts.
    """
    service = get_a2a_service()
    task = service.get_task(task_id, history_length)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "task_not_found",
                "message": f"Task {task_id} not found"
            }
        )
    
    # Verify user access
    if task.metadata.get("user_id") != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return task.dict()


@router.get("/tasks")
async def list_tasks(
    context_id: Optional[str] = Query(None),
    status: Optional[TaskState] = Query(None),
    page_size: int = Query(50, ge=1, le=100),
    page_token: Optional[str] = Query(None),
    user: User = Depends(get_current_user)
):
    """
    List tasks with optional filtering.
    
    Supports pagination and filtering by context, status.
    """
    service = get_a2a_service()
    
    # Regular users only see their own tasks
    user_id = None if user.role == "admin" else user.id
    
    response = service.list_tasks(
        context_id=context_id,
        status=status,
        page_size=page_size,
        page_token=page_token,
        user_id=user_id
    )
    
    return response.dict()


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    user: User = Depends(get_current_user)
):
    """
    Cancel a running task.
    
    Returns the updated task state.
    """
    service = get_a2a_service()
    
    # Verify task exists and user has access
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "task_not_found",
                "message": f"Task {task_id} not found"
            }
        )
    
    if task.metadata.get("user_id") != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = service.cancel_task(task_id)
    
    if not result:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "task_not_cancelable",
                "message": "Task cannot be canceled (already completed or failed)"
            }
        )
    
    return result.dict()


@router.get("/tasks/{task_id}/subscribe")
async def subscribe_to_task(
    task_id: str,
    req: Request,
    user: User = Depends(get_current_user)
):
    """
    Subscribe to task updates via SSE.
    
    Streams task status and artifact updates until task completes.
    """
    service = get_a2a_service()
    
    # Verify task exists and user has access
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "task_not_found",
                "message": f"Task {task_id} not found"
            }
        )
    
    if task.metadata.get("user_id") != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    async def event_generator():
        # Send initial task state
        yield {
            "event": "message",
            "data": json.dumps({"task": task.dict()}, ensure_ascii=False)
        }
        
        # Poll for updates (simple implementation)
        import asyncio
        last_updated = task.updated_at
        
        for _ in range(300):  # Max 5 minutes
            await asyncio.sleep(1)
            
            current_task = service.get_task(task_id)
            if not current_task:
                break
            
            if current_task.updated_at != last_updated:
                last_updated = current_task.updated_at
                yield {
                    "event": "status_update",
                    "data": json.dumps({
                        "task_id": task_id,
                        "status": current_task.status.dict()
                    }, ensure_ascii=False)
                }
            
            # Check if terminal state
            if current_task.status.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED, TaskState.REJECTED):
                yield {
                    "event": "complete",
                    "data": json.dumps({"task": current_task.dict()}, ensure_ascii=False)
                }
                break
    
    return EventSourceResponse(event_generator())


# ============================================================================
# JSON-RPC 2.0 Endpoint (Optional)
# ============================================================================

@router.post("/rpc")
async def json_rpc_endpoint(
    request: dict,
    req: Request,
    user: User = Depends(get_current_user)
):
    """
    JSON-RPC 2.0 endpoint for A2A operations.
    
    Supports standard JSON-RPC 2.0 request/response format.
    """
    import json
    
    # Validate JSON-RPC request
    if request.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid Request"},
            "id": request.get("id")
        }
    
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")
    
    service = get_a2a_service()
    base_url = get_base_url(req)
    
    try:
        if method == "getAgentCard":
            result = service.get_agent_card(base_url).dict()
        elif method == "sendMessage":
            msg_request = SendMessageRequest(**params)
            response = await service.send_message(msg_request, user.id, base_url)
            result = response.dict(exclude_none=True)
        elif method == "getTask":
            task = service.get_task(params.get("task_id"), params.get("history_length"))
            result = task.dict() if task else None
        elif method == "listTasks":
            response = service.list_tasks(
                context_id=params.get("context_id"),
                status=params.get("status"),
                page_size=params.get("page_size", 50),
                page_token=params.get("page_token"),
                user_id=None if user.role == "admin" else user.id
            )
            result = response.dict()
        elif method == "cancelTask":
            task = service.cancel_task(params.get("task_id"))
            result = task.dict() if task else None
        else:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id
            }
        
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
        
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": request_id
        }