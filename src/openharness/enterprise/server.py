"""
OpenHarness Enterprise - Main Server

FastAPI application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Optional, List, Dict, Any

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, Query, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from pathlib import Path
import shutil
import uuid
import zipfile

from openharness.enterprise.storage.database import (
    User, Session, AuditLog,
    get_database, init_database
)
from openharness.enterprise.storage.audit import get_audit_logger
from openharness.enterprise.auth.auth import (
    AuthError,
    get_auth_service,
    get_internal_auth_service,
    get_user_manager,
)
from openharness.enterprise.auth.middleware import (
    AuthMiddleware,
    WorkspaceIsolationMiddleware,
    get_current_user,
    require_admin,
)
from openharness.enterprise.users.workspace import (
    get_workspace_manager,
    get_enterprise_root,
    get_shared_root,
)
from openharness.enterprise.users.context import load_user_context
from openharness.enterprise.channels.webchat import get_webchat_channel
from openharness.enterprise.agents.registry import (
    AgentConfig, AgentRole, TeamConfig, get_agent_registry
)
from openharness.enterprise.agents.coordinator import (
    get_team_coordinator, TeamSession
)
from openharness.enterprise.tools.registry import (
    ToolCategory,
    ToolPermission,
    ToolParameter,
    ToolDefinition,
    ToolResult,
    ToolExecutor,
    ToolRegistry,
    get_tool_registry,
)


# ============================================================================
# Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("[*] Starting OpenHarness Enterprise...")
    
    # Initialize database
    db = init_database()
    print(f"[+] Database initialized at {get_enterprise_root() / 'data.db'}")
    
    # Initialize workspace manager
    get_workspace_manager()
    print(f"[+] Workspace root: {get_enterprise_root() / 'users'}")
    
    # Ensure admin user exists
    _ensure_admin_user()
    
    # [新增] Initialize Meditate scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from openharness.enterprise.users.meditate import get_meditate_scheduler
        
        scheduler = AsyncIOScheduler()
        
        # 每天凌晨 3:00 执行 Meditate
        scheduler.add_job(
            _run_meditate_daily,
            'cron',
            hour=3,
            minute=0,
            id='meditate_daily'
        )
        
        scheduler.start()
        app.state.scheduler = scheduler
        print("[+] Meditate scheduler started (daily at 3:00 AM)")
    except ImportError:
        print("[!] APScheduler not installed, Meditate scheduler disabled")
    except Exception as e:
        print(f"[!] Meditate scheduler error: {e}")
    
    print("[OK] OpenHarness Enterprise ready!")
    
    yield
    
    # Shutdown
    print("[*] Shutting down OpenHarness Enterprise...")


def _run_meditate_daily():
    """每日 Meditate 任务"""
    from openharness.enterprise.users.meditate import get_meditate_scheduler
    
    print("[Meditate] Starting daily meditate...")
    scheduler = get_meditate_scheduler()
    results = scheduler.run_daily()
    print(f"[Meditate] Completed: {len(results)} users processed")


def _ensure_admin_user() -> None:
    """Ensure admin user exists."""
    db = get_database()
    user_manager = get_user_manager()
    
    if not db.user_exists("admin"):
        try:
            user = user_manager.create_user(
                username="admin",
                password="admin123",
                display_name="Administrator",
                role="admin"
            )
            print(f"[+] Created default admin user: admin / admin123")
            print(f"[KEY] Admin API Key: {user.api_key}")
        except Exception as e:
            print(f"[!] Failed to create admin user: {e}")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="OpenHarness Enterprise",
    description="Multi-user enterprise version of OpenHarness",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware (disabled for public paths)
# app.add_middleware(AuthMiddleware)
# app.add_middleware(WorkspaceIsolationMiddleware)

# ============================================================================
# A2A Protocol Routes
# ============================================================================

from openharness.enterprise.a2a.routes import router as a2a_router
app.include_router(a2a_router)


# ============================================================================
# Request Models
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class ApiKeyTokenRequest(BaseModel):
    api_key: str
    expires_in: Optional[int] = None


class CreateUserRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: str = "user"


class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0-enterprise"}


# ============================================================================
# Auth Routes
# ============================================================================

@app.post("/api/auth/login")
async def login(request: LoginRequest, req: Request):
    """User login."""
    auth_service = get_auth_service()
    ip_address = req.client.host if req.client else None
    
    try:
        result = auth_service.login(
            username=request.username,
            password=request.password,
            ip_address=ip_address
        )
        return result
    except AuthError as e:
        raise HTTPException(status_code=401, detail=e.message)


@app.post("/api/auth/token-by-api-key")
async def get_token_by_api_key(request: ApiKeyTokenRequest, req: Request):
    """Get token by API key (for embedding scenarios)."""
    internal_auth = get_internal_auth_service()
    ip_address = req.client.host if req.client else None
    
    try:
        result = internal_auth.get_token_by_api_key(
            api_key=request.api_key,
            expires_in=request.expires_in,
            ip_address=ip_address
        )
        return result
    except AuthError as e:
        raise HTTPException(status_code=401, detail=e.message)


@app.get("/api/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "api_key": user.api_key,
        "api_key_enabled": user.api_key_enabled
    }


# ============================================================================
# User Routes (Self-management)
# ============================================================================

@app.get("/api/user/me/api-key")
async def get_my_api_key(user: User = Depends(get_current_user)):
    """Get my API key."""
    return {
        "api_key": user.api_key,
        "api_key_enabled": user.api_key_enabled,
        "last_api_key_used_at": user.last_api_key_used_at
    }


@app.post("/api/user/me/api-key/regenerate")
async def regenerate_my_api_key(user: User = Depends(get_current_user)):
    """Regenerate my API key."""
    user_manager = get_user_manager()
    new_key = user_manager.regenerate_api_key(user.id)
    return {
        "api_key": new_key,
        "message": "旧 API Key 已失效，请保存新 Key"
    }


# ============================================================================
# Admin Routes
# ============================================================================

@app.get("/api/admin/users")
async def list_users(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: User = Depends(require_admin)
):
    """List users (admin only)."""
    db = get_database()
    users = db.list_users(search=search, page=page, limit=limit)
    total = db.count_users(search=search)
    
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "display_name": u.display_name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "api_key_enabled": u.api_key_enabled,
                "created_at": u.created_at,
                "last_login_at": u.last_login_at
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@app.post("/api/admin/users")
async def create_user(
    request: CreateUserRequest,
    admin: User = Depends(require_admin)
):
    """Create user (admin only)."""
    user_manager = get_user_manager()
    workspace_manager = get_workspace_manager()
    audit = get_audit_logger()
    
    try:
        user = user_manager.create_user(
            username=request.username,
            password=request.password,
            display_name=request.display_name,
            email=request.email,
            role=request.role
        )
        
        # Initialize workspace
        workspace_manager.init_workspace(user)
        
        # Audit log
        audit.log_admin_action(admin.id, "create_user", user.id, {
            "username": user.username,
            "role": user.role
        })
        
        return {
            "id": user.id,
            "username": user.username,
            "api_key": user.api_key,
            "message": "用户创建成功"
        }
    except AuthError as e:
        raise HTTPException(status_code=400, detail=e.message)


@app.get("/api/admin/users/{user_id}")
async def get_user(user_id: int, admin: User = Depends(require_admin)):
    """Get user details (admin only)."""
    db = get_database()
    user = db.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "api_key": user.api_key,
        "api_key_enabled": user.api_key_enabled,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at
    }


@app.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    admin: User = Depends(require_admin)
):
    """Update user (admin only)."""
    db = get_database()
    user_manager = get_user_manager()
    audit = get_audit_logger()
    
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    updated_user = user_manager.update_user(
        user_id=user_id,
        display_name=request.display_name,
        email=request.email,
        role=request.role,
        is_active=request.is_active
    )
    
    audit.log_admin_action(admin.id, "update_user", user_id, request.dict())
    
    return {
        "id": updated_user.id,
        "username": updated_user.username,
        "message": "用户更新成功"
    }


@app.delete("/api/admin/users/{user_id}")
async def disable_user(user_id: int, admin: User = Depends(require_admin)):
    """Disable user (admin only)."""
    db = get_database()
    audit = get_audit_logger()
    
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    db.update_user(user_id, is_active=False)
    audit.log_admin_action(admin.id, "disable_user", user_id)
    
    return {"status": "disabled", "message": "用户已禁用"}


@app.get("/api/admin/users/{user_id}/api-key")
async def get_user_api_key(user_id: int, admin: User = Depends(require_admin)):
    """Get user API key (admin only)."""
    db = get_database()
    user = db.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "api_key": user.api_key,
        "api_key_enabled": user.api_key_enabled,
        "last_api_key_used_at": user.last_api_key_used_at
    }


@app.post("/api/admin/users/{user_id}/api-key/regenerate")
async def regenerate_user_api_key(user_id: int, admin: User = Depends(require_admin)):
    """Regenerate user API key (admin only)."""
    db = get_database()
    user_manager = get_user_manager()
    
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    new_key = user_manager.regenerate_api_key(user_id)
    
    return {
        "api_key": new_key,
        "message": "API Key 已重新生成"
    }


@app.get("/api/admin/system/status")
async def get_system_status(admin: User = Depends(require_admin)):
    """Get system status (admin only)."""
    db = get_database()
    
    return {
        "total_users": db.count_users(),
        "active_sessions": db.count_active_sessions(),
        "db_size": db.get_db_size(),
        "workspace_root": str(get_enterprise_root())
    }


@app.get("/api/admin/audit-logs")
async def query_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 50,
    admin: User = Depends(require_admin)
):
    """Query audit logs (admin only)."""
    db = get_database()
    logs = db.query_audit_logs(
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at
            }
            for log in logs
        ],
        "page": page,
        "limit": limit
    }


# ============================================================================
# WebSocket Routes
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(...),
    session_id: Optional[str] = Query(None)
):
    """
    WebSocket chat endpoint.
    
    Query Parameters:
        token: JWT authentication token
        session_id: Optional session ID to resume
    
    Message Format (Client -> Server):
        {
            "type": "message" | "command" | "resume",
            "payload": { "content": "...", ... }
        }
    
    Message Format (Server -> Client):
        {
            "type": "text" | "tool_call" | "thinking" | "error" | "done" | "session_info",
            "payload": { ... },
            "session_id": "...",
            "timestamp": "..."
        }
    """
    # Authenticate via token
    auth_service = get_auth_service()
    
    try:
        payload = auth_service.verify_token(token)
        user_id = payload["user_id"]
    except AuthError as e:
        await websocket.close(code=4001, reason=e.message)
        return
    
    # Get user
    db = get_database()
    user = db.get_user(user_id)
    
    if not user or not user.is_active:
        await websocket.close(code=4001, reason="User not found or inactive")
        return
    
    # Handle connection
    channel = get_webchat_channel()
    await channel.handle_connection(
        websocket=websocket,
        user=user,
        session_id=session_id
    )


@app.get("/api/sessions")
async def list_sessions(
    user: User = Depends(get_current_user)
):
    """List user's sessions."""
    db = get_database()
    sessions = db.get_user_sessions(user.id)
    
    return {
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "message_count": s.message_count,
                "is_active": s.is_active,
                "created_at": s.created_at,
                "updated_at": s.updated_at
            }
            for s in sessions
        ]
    }


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 100,
    user: User = Depends(get_current_user)
):
    """Get messages for a session."""
    db = get_database()
    
    # Verify session belongs to user
    session = db.get_session(session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.get_session_messages(session_id, limit)
    
    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tokens_used": m.tokens_used,
                "created_at": m.created_at
            }
            for m in messages
        ]
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user)
):
    """Delete (archive) a session."""
    db = get_database()
    audit = get_audit_logger()
    
    # Verify session belongs to user
    session = db.get_session(session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Mark session as inactive (soft delete)
    db.update_session(session_id, is_active=False)
    
    audit.log(
        user_id=user.id,
        action="delete_session",
        resource_type="session",
        resource_id=session_id
    )
    
    return {"status": "deleted", "message": "会话已删除"}


# ============================================================================
# Context & Session Restore API [新增]
# ============================================================================

@app.get("/api/context")
async def get_user_context(
    user: User = Depends(get_current_user)
):
    """[新增] 获取当前用户完整上下文"""
    from openharness.enterprise.users.context import load_user_context
    from openharness.enterprise.users.memory import get_memory_manager
    
    context = load_user_context(user)
    memory_mgr = get_memory_manager(user.id)
    
    return {
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "soul": context.soul,
        "identity": context.identity,
        "user_profile": context.user_profile,
        "has_bootstrap": bool(context.bootstrap),
        "memory": {
            "long_term": memory_mgr.read_memory(),
            "recent_daily": memory_mgr.read_all_daily(limit=7)
        },
        "preferences": context.preferences
    }


@app.post("/api/sessions/{session_id}/restore")
async def restore_session(
    session_id: str,
    user: User = Depends(get_current_user)
):
    """[新增] 恢复会话完整上下文"""
    from openharness.enterprise.users.restorer import get_session_restorer
    
    restorer = get_session_restorer(user.id)
    result = restorer.restore_session(session_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    session = result["session"]
    messages = result["messages"]
    
    return {
        "session_id": session.id,
        "title": session.title,
        "model": session.model,
        "session_key": session.session_key,
        "system_prompt": result["system_prompt"],
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at
            }
            for m in messages
        ],
        "restored": True
    }


@app.get("/api/sessions/resumable")
async def get_resumable_sessions(
    limit: int = 10,
    user: User = Depends(get_current_user)
):
    """[新增] 获取可恢复的会话列表"""
    from openharness.enterprise.users.restorer import get_session_restorer
    
    restorer = get_session_restorer(user.id)
    sessions = restorer.get_resumable_sessions(limit)
    
    return {"sessions": sessions}


@app.post("/api/learning/extract")
async def trigger_learning(
    user: User = Depends(get_current_user)
):
    """[新增] 手动触发用户信息提取（从最近对话）"""
    from openharness.enterprise.users.learning import get_learning_engine
    
    db = get_database()
    sessions = db.get_user_sessions(user.id, limit=3)
    
    if not sessions:
        return {"status": "skipped", "reason": "no_conversations"}
    
    # 获取最近对话的消息
    all_messages = []
    for session in sessions:
        messages = db.get_session_messages(session.id, limit=20)
        all_messages.extend([
            {"role": m.role, "content": m.content}
            for m in messages
        ])
    
    learning_engine = get_learning_engine(user.id)
    user_info = learning_engine.extract_user_info(all_messages)
    
    if user_info:
        learning_engine.update_user_profile(user_info)
        return {"status": "success", "extracted": user_info}
    
    return {"status": "skipped", "reason": "no_info_found"}


# ============================================================================
# Meditate API [新增]
# ============================================================================

@app.post("/api/meditate")
async def trigger_meditate(
    date: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """[新增] 手动触发 Meditate（记忆反思与整合）"""
    from openharness.enterprise.users.meditate import get_meditate_executor
    
    executor = get_meditate_executor(user.id)
    result = await executor.execute_async(date)
    
    return result


@app.post("/api/meditate/all")
async def trigger_meditate_all(
    user: User = Depends(require_admin)
):
    """[新增] 管理员触发所有用户的 Meditate"""
    from openharness.enterprise.users.meditate import get_meditate_scheduler
    
    scheduler = get_meditate_scheduler()
    results = await scheduler.run_daily_async()
    
    return {
        "status": "completed",
        "users_processed": len(results),
        "results": results
    }


# ============================================================================
# Skills API
# ============================================================================

def _scan_skills_directory(directory: Path) -> List[Dict[str, Any]]:
    """Scan a directory for skills."""
    skills = []
    if not directory.exists():
        return skills
    
    for skill_dir in directory.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                try:
                    content = skill_file.read_text(encoding="utf-8")
                    
                    # Extract title from first heading
                    title = skill_dir.name
                    for line in content.split("\n")[:10]:
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break
                    
                    # Extract description from YAML front matter
                    description = ""
                    if content.startswith("---"):
                        # Find the end of front matter
                        end_idx = content.find("---", 3)
                        if end_idx != -1:
                            front_matter = content[3:end_idx].strip()
                            # Parse description from front matter
                            for line in front_matter.split("\n"):
                                if line.startswith("description:"):
                                    # Handle both quoted and unquoted descriptions
                                    desc_value = line[len("description:"):].strip()
                                    # Remove quotes if present
                                    if desc_value.startswith('"') and desc_value.endswith('"'):
                                        description = desc_value[1:-1]
                                    elif desc_value.startswith("'") and desc_value.endswith("'"):
                                        description = desc_value[1:-1]
                                    else:
                                        description = desc_value
                                    break
                    
                    # Count files in skill directory
                    file_count = len([f for f in skill_dir.iterdir() if f.is_file()])
                    
                    skills.append({
                        "name": skill_dir.name,
                        "title": title,
                        "description": description,
                        "path": str(skill_dir),
                        "type": "skill",
                        "has_skill_md": True,
                        "file_count": file_count
                    })
                except Exception:
                    pass
    
    return skills


@app.get("/api/skills")
async def list_skills(user: User = Depends(get_current_user)):
    """List available skills (personal + shared)."""
    # Get user's personal skills
    user_skills_path = get_enterprise_root() / "users" / str(user.id) / "skills"
    personal_skills = _scan_skills_directory(user_skills_path)
    
    # Get shared skills
    shared_skills_path = get_shared_root() / "skills"
    shared_skills = _scan_skills_directory(shared_skills_path)
    
    # Check permissions for shared skills
    db = get_database()
    available_shared = []
    for skill in shared_skills:
        if db.user_can_access(user.id, "skill", skill["name"]):
            available_shared.append(skill)
    
    return {
        "personal": personal_skills,
        "shared": available_shared
    }


@app.get("/api/skills/manage")
async def list_manageable_skills(user: User = Depends(get_current_user)):
    """
    List all skills the user can manage.
    
    - Admin: sees shared skills + personal skills
    - Regular user: sees shared skills + personal skills
    """
    shared_skills_path = get_shared_root() / "skills"
    shared_skills = _scan_skills_directory(shared_skills_path)
    
    # 所有用户都能看到自己的个人技能
    user_skills_path = get_enterprise_root() / "users" / str(user.id) / "skills"
    personal_skills = _scan_skills_directory(user_skills_path)
    
    result = {
        "shared": shared_skills,
        "personal": personal_skills,
        "is_admin": user.role == "admin"
    }
    
    return result


@app.post("/api/skills/reload")
async def reload_skills(user: User = Depends(get_current_user)):
    """Reload skills list (after adding new skills)."""
    # Force reload by returning fresh scan
    user_skills_path = get_enterprise_root() / "users" / str(user.id) / "skills"
    shared_skills_path = get_shared_root() / "skills"
    
    personal_skills = _scan_skills_directory(user_skills_path)
    shared_skills = _scan_skills_directory(shared_skills_path)
    
    return {
        "message": "Skills reloaded",
        "personal_count": len(personal_skills),
        "shared_count": len(shared_skills),
        "personal_skills": [s["name"] for s in personal_skills],
        "shared_skills": [s["name"] for s in shared_skills]
    }


@app.post("/api/skills/upload")
async def upload_personal_skill(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """
    Upload a personal skill.
    
    - Admin: uploads to shared directory
    - Regular user: uploads to personal directory
    - Regular user: skill name cannot duplicate shared skill names
    """
    import zipfile
    import shutil
    
    # Validate file type
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="只支持 ZIP 文件格式")
    
    # Extract skill name from filename
    skill_name = file.filename[:-4]
    
    # Determine upload path based on role
    if user.role == "admin":
        skills_path = get_shared_root() / "skills"
        skill_type = "shared"
    else:
        skills_path = get_enterprise_root() / "users" / str(user.id) / "skills"
        skill_type = "personal"
        
        # [新增] 普通用户上传时检查是否与共享技能重复
        shared_skills_path = get_shared_root() / "skills"
        shared_skill_names = [s["name"] for s in _scan_skills_directory(shared_skills_path)]
        if skill_name in shared_skill_names:
            raise HTTPException(
                status_code=400, 
                detail=f"技能名称 '{skill_name}' 与共享技能重复，请使用其他名称"
            )
    
    skills_path.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file temporarily
    temp_zip_path = skills_path / f"temp_{file.filename}"
    
    try:
        # Write uploaded file
        with open(temp_zip_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract skill name from filename
        skill_name = file.filename[:-4]
        skill_path = skills_path / skill_name
        
        # Check if skill already exists
        if skill_path.exists():
            shutil.rmtree(skill_path)
        
        # Extract ZIP
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(skills_path)
        
        # Clean up ZIP file
        temp_zip_path.unlink()
        
        # Reload skills
        await reload_skills(user)
        
        return {
            "success": True,
            "message": f"技能 {skill_name} 上传成功",
            "skill_name": skill_name,
            "type": skill_type,
            "path": str(skill_path)
        }
        
    except zipfile.BadZipFile:
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        raise HTTPException(status_code=400, detail="无效的 ZIP 文件")
    except Exception as e:
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.delete("/api/skills/{skill_name}")
async def delete_skill(
    skill_name: str,
    skill_type: str = Query("personal", description="Skill type: 'personal' or 'shared'"),
    user: User = Depends(get_current_user)
):
    """
    Delete a skill.
    
    - Admin: can delete shared skills
    - Regular user: can only delete personal skills
    """
    import shutil
    
    # Regular users can only delete personal skills
    if user.role != "admin" and skill_type == "shared":
        raise HTTPException(status_code=403, detail="无权删除共享技能")
    
    # Determine skill path
    if skill_type == "shared":
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="无权删除共享技能")
        skill_path = get_shared_root() / "skills" / skill_name
    else:
        skill_path = get_enterprise_root() / "users" / str(user.id) / "skills" / skill_name
    
    if not skill_path.exists():
        raise HTTPException(status_code=404, detail="技能不存在")
    
    try:
        shutil.rmtree(skill_path)
        return {"success": True, "message": f"技能 {skill_name} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@app.get("/api/skills/{skill_name}")
async def get_skill(skill_name: str, user: User = Depends(get_current_user)):
    """Get skill content."""
    # Check personal skills first
    user_skill_path = get_enterprise_root() / "users" / str(user.id) / "skills" / skill_name / "SKILL.md"
    if user_skill_path.exists():
        return {
            "name": skill_name,
            "content": user_skill_path.read_text(encoding="utf-8"),
            "type": "personal"
        }
    
    # Check shared skills
    db = get_database()
    if not db.user_can_access(user.id, "skill", skill_name):
        raise HTTPException(status_code=404, detail="Skill not found")
    
    shared_skill_path = get_shared_root() / "skills" / skill_name / "SKILL.md"
    if shared_skill_path.exists():
        return {
            "name": skill_name,
            "content": shared_skill_path.read_text(encoding="utf-8"),
            "type": "shared"
        }
    
    raise HTTPException(status_code=404, detail="Skill not found")


# ============================================================================
# Admin Skills API
# ============================================================================

@app.get("/api/admin/skills")
async def admin_list_skills(admin: User = Depends(require_admin)):
    """List all skills (admin only)."""
    shared_skills_path = get_shared_root() / "skills"
    shared_skills = _scan_skills_directory(shared_skills_path)
    
    return {
        "shared": shared_skills
    }


@app.post("/api/admin/skills/upload")
async def admin_upload_skill(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin)
):
    """
    Upload a skill (admin only).
    
    Uploads to shared skills directory.
    Accepts ZIP file, extracts it, and deletes the ZIP.
    """
    import zipfile
    import shutil
    
    # Validate file type
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="只支持 ZIP 文件格式")
    
    # Get shared skills path
    shared_skills_path = get_shared_root() / "skills"
    shared_skills_path.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file temporarily
    temp_zip_path = shared_skills_path / f"temp_{file.filename}"
    
    try:
        # Write uploaded file
        with open(temp_zip_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract skill name from filename (remove .zip extension)
        skill_name = file.filename[:-4]
        skill_path = shared_skills_path / skill_name
        
        # Check if skill already exists
        if skill_path.exists():
            shutil.rmtree(skill_path)
        
        # Extract ZIP
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(shared_skills_path)
        
        # Check if SKILL.md exists
        extracted_skill_path = None
        for item in shared_skills_path.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                extracted_skill_path = item
                break
        
        # Clean up ZIP file
        temp_zip_path.unlink()
        
        # Reload skills
        await reload_skills(admin)
        
        return {
            "success": True,
            "message": f"技能 {skill_name} 上传成功",
            "skill_name": skill_name,
            "path": str(skill_path)
        }
        
    except zipfile.BadZipFile:
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        raise HTTPException(status_code=400, detail="无效的 ZIP 文件")
    except Exception as e:
        if temp_zip_path.exists():
            temp_zip_path.unlink()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.delete("/api/admin/skills/{skill_name}")
async def admin_delete_skill(
    skill_name: str,
    admin: User = Depends(require_admin)
):
    """Delete a skill from shared directory (admin only)."""
    import shutil
    
    skill_path = get_shared_root() / "skills" / skill_name
    
    if not skill_path.exists():
        raise HTTPException(status_code=404, detail="技能不存在")
    
    try:
        shutil.rmtree(skill_path)
        return {"success": True, "message": f"技能 {skill_name} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@app.post("/api/admin/skills/{skill_name}/permissions")
async def set_skill_permission(
    skill_name: str,
    user_ids: Optional[List[int]] = None,
    admin: User = Depends(require_admin)
):
    """Set skill access permissions (admin only)."""
    db = get_database()
    
    # Clear existing permissions
    # Note: This is simplified - in production you'd want more granular control
    if user_ids is None:
        # Everyone can access
        db.set_permission("skill", skill_name, None, "read")
    else:
        # Only specific users
        for uid in user_ids:
            db.set_permission("skill", skill_name, uid, "read")
    
    return {
        "skill": skill_name,
        "allowed_users": user_ids,
        "message": "Permissions updated"
    }


# ============================================================================
# Agents API
# ============================================================================

@app.get("/api/agents")
async def list_agents(user: User = Depends(get_current_user)):
    """List all available agents."""
    registry = get_agent_registry()
    agents = registry.list_agents()
    
    return {
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role.value,
                "description": a.description,
                "model": a.model,
                "is_active": a.is_active
            }
            for a in agents
        ]
    }


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str, user: User = Depends(get_current_user)):
    """Get agent details."""
    registry = get_agent_registry()
    agent = registry.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role.value,
        "description": agent.description,
        "system_prompt": agent.system_prompt,
        "model": agent.model,
        "max_tokens": agent.max_tokens,
        "temperature": agent.temperature,
        "is_active": agent.is_active
    }


@app.put("/api/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    user: User = Depends(get_current_user)
):
    """Update agent configuration."""
    registry = get_agent_registry()
    
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if system_prompt is not None:
        kwargs["system_prompt"] = system_prompt
    if model is not None:
        kwargs["model"] = model
    if temperature is not None:
        kwargs["temperature"] = temperature
    
    agent = registry.update_agent(agent_id, **kwargs)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "id": agent.id,
        "name": agent.name,
        "message": "Agent updated"
    }


@app.post("/api/agents")
async def create_agent(
    id: str = Body(...),
    name: str = Body(...),
    system_prompt: str = Body(...),
    description: Optional[str] = Body(None),
    role: str = Body("custom"),
    model: str = Body("glm-5"),
    temperature: float = Body(0.7),
    user: User = Depends(get_current_user)
):
    """Create a custom agent."""
    registry = get_agent_registry()
    
    # Check if agent already exists
    if registry.get_agent(id):
        raise HTTPException(status_code=400, detail="Agent ID already exists")
    
    agent = AgentConfig(
        id=id,
        name=name,
        role=AgentRole(role),
        description=description or "",
        system_prompt=system_prompt,
        model=model,
        temperature=temperature
    )
    
    created = registry.create_agent(agent)
    
    return {
        "id": created.id,
        "name": created.name,
        "message": "Agent created"
    }


# ============================================================================
# Teams API
# ============================================================================

@app.get("/api/teams")
async def list_teams(user: User = Depends(get_current_user)):
    """List all available teams."""
    registry = get_agent_registry()
    teams = registry.list_teams()
    
    return {
        "teams": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "agents": t.agents,
                "workflow": t.workflow,
                "is_active": t.is_active
            }
            for t in teams
        ]
    }


@app.get("/api/teams/{team_id}")
async def get_team(team_id: str, user: User = Depends(get_current_user)):
    """Get team details with agent info."""
    registry = get_agent_registry()
    team = registry.get_team(team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    agents = registry.get_team_agents(team_id)
    
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "workflow": team.workflow,
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role.value
            }
            for a in agents
        ]
    }


@app.post("/api/teams")
async def create_team(
    id: str = Body(...),
    name: str = Body(...),
    agents: List[str] = Body(...),
    description: Optional[str] = Body(None),
    workflow: str = Body("sequential"),
    user: User = Depends(get_current_user)
):
    """Create a custom team."""
    registry = get_agent_registry()
    
    if registry.get_team(id):
        raise HTTPException(status_code=400, detail="Team ID already exists")
    
    team = TeamConfig(
        id=id,
        name=name,
        description=description or "",
        agents=agents,
        workflow=workflow
    )
    
    created = registry.create_team(team)
    
    return {
        "id": created.id,
        "name": created.name,
        "message": "Team created"
    }


@app.put("/api/teams/{team_id}")
async def update_team(
    team_id: str,
    name: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    agents: Optional[List[str]] = Body(None),
    workflow: Optional[str] = Body(None),
    user: User = Depends(get_current_user)
):
    """Update team configuration."""
    registry = get_agent_registry()
    
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if agents is not None:
        kwargs["agents"] = agents
    if workflow is not None:
        kwargs["workflow"] = workflow
    
    team = registry.update_team(team_id, **kwargs)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {
        "id": team.id,
        "name": team.name,
        "message": "Team updated"
    }


@app.delete("/api/teams/{team_id}")
async def delete_team(team_id: str, user: User = Depends(get_current_user)):
    """Delete a team."""
    registry = get_agent_registry()
    
    if not registry.delete_team(team_id):
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {"message": "Team deleted"}


# ============================================================================
# Team Execution API
# ============================================================================

@app.post("/api/teams/{team_id}/run")
async def run_team(
    team_id: str,
    task: str = Body(...),
    context: Optional[Dict[str, Any]] = Body(None),
    user: User = Depends(get_current_user)
):
    """Run a team task (returns session ID for WebSocket)."""
    coordinator = get_team_coordinator()
    registry = get_agent_registry()
    
    team = registry.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    session = coordinator.create_session(team_id, task, context)
    
    return {
        "session_id": session.id,
        "team_id": team_id,
        "task": task,
        "status": "created",
        "message": "Session created. Connect to WebSocket to receive messages."
    }


@app.get("/api/team-sessions/{session_id}")
async def get_team_session(session_id: str, user: User = Depends(get_current_user)):
    """Get team session status and results."""
    coordinator = get_team_coordinator()
    summary = coordinator.get_session_summary(session_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return summary


@app.websocket("/ws/team/{session_id}")
async def websocket_team(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for team execution.
    
    Streams messages from all agents in the team.
    """
    # Authenticate
    auth_service = get_auth_service()
    try:
        payload = auth_service.verify_token(token)
        user_id = payload["user_id"]
    except AuthError as e:
        await websocket.close(code=4001, reason=e.message)
        return
    
    # Get session
    coordinator = get_team_coordinator()
    session = coordinator.get_session(session_id)
    
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    await websocket.accept()
    
    # Send session info
    await websocket.send_json({
        "type": "session_start",
        "session_id": session_id,
        "team_id": session.team_id,
        "task": session.task
    })
    
    # Run team and stream messages
    try:
        async for msg in coordinator.run_sequential(session):
            await websocket.send_json({
                "type": "agent_message",
                "agent_id": msg.agent_id,
                "agent_name": msg.agent_name,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            })
        
        # Send completion
        await websocket.send_json({
            "type": "session_complete",
            "session_id": session_id,
            "status": session.status,
            "message_count": len(session.messages)
        })
        
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    
    await websocket.close()


# ============================================================================
# Tools API
# ============================================================================

@app.get("/api/tools")
async def list_tools(
    category: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """List all available tools."""
    registry = get_tool_registry()
    tools = registry.list_tools(category=category)
    
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category.value,
                "permission": t.permission.value,
                "is_dangerous": t.is_dangerous,
                "is_enabled": t.is_enabled,
                "parameters": {
                    k: {
                        "type": v.type,
                        "description": v.description,
                        "required": v.required
                    }
                    for k, v in t.parameters.items()
                }
            }
            for t in tools
        ]
    }


@app.get("/api/tools/{tool_name}")
async def get_tool(tool_name: str, user: User = Depends(get_current_user)):
    """Get tool details."""
    registry = get_tool_registry()
    tool = registry.get_tool(tool_name)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return {
        "name": tool.name,
        "description": tool.description,
        "category": tool.category.value,
        "permission": tool.permission.value,
        "is_dangerous": tool.is_dangerous,
        "is_enabled": tool.is_enabled,
        "parameters": {
            k: {
                "type": v.type,
                "description": v.description,
                "required": v.required,
                "default": v.default
            }
            for k, v in tool.parameters.items()
        },
        "returns": tool.returns,
        "timeout": tool.timeout
    }


@app.get("/api/tools/schemas")
async def get_tool_schemas(user: User = Depends(get_current_user)):
    """Get all tool schemas for LLM function calling."""
    registry = get_tool_registry()
    schemas = registry.get_all_schemas()
    return {"tools": schemas}


@app.post("/api/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    user: User = Depends(get_current_user)
):
    """Execute a tool."""
    registry = get_tool_registry()
    audit = get_audit_logger()
    
    # Check if tool exists and is enabled
    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if not tool.is_enabled:
        raise HTTPException(status_code=403, detail="Tool is disabled")
    
    # Log tool execution
    audit.log(
        user_id=user.id,
        action="tool_execute",
        resource_type="tool",
        resource_id=tool_name,
        details={"parameters": parameters}
    )
    
    # Execute tool
    result = registry.execute_tool(tool_name, parameters)
    
    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "execution_time": result.execution_time
    }


@app.put("/api/tools/{tool_name}/enabled")
async def set_tool_enabled(
    tool_name: str,
    enabled: bool,
    user: User = Depends(require_admin)
):
    """Enable or disable a tool (admin only)."""
    registry = get_tool_registry()
    
    tool = registry.update_tool(tool_name, is_enabled=enabled)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return {
        "name": tool.name,
        "is_enabled": tool.is_enabled
    }


@app.post("/api/tools/custom")
async def create_custom_tool(
    name: str,
    description: str,
    parameters: Dict[str, Dict],
    user: User = Depends(require_admin)
):
    """Create a custom tool (admin only)."""
    registry = get_tool_registry()
    
    if registry.get_tool(name):
        raise HTTPException(status_code=400, detail="Tool already exists")
    
    tool = registry.register_custom_tool(
        name=name,
        description=description,
        parameters=parameters
    )
    
    return {
        "name": tool.name,
        "message": "Tool created"
    }


# ============================================================================
# File Upload API
# ============================================================================

ALLOWED_EXTENSIONS = {'.txt', '.md', '.png', '.jpg', '.jpeg', '.docx', '.xlsx', '.csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def get_user_upload_dir(user_id: int) -> Path:
    """Get user's upload directory."""
    upload_dir = get_enterprise_root() / "users" / str(user_id) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """
    Upload a file to user's upload directory.
    
    Supported file types: .txt, .md, .png, .jpg, .jpeg, .docx, .xlsx, .csv
    Max file size: 10MB
    """
    audit = get_audit_logger()
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type '{file_ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Use original filename (keep it unchanged)
    filename = file.filename
    
    # Save file
    upload_dir = get_user_upload_dir(user.id)
    file_path = upload_dir / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Log audit
    audit.log(
        user_id=user.id,
        action="file_upload",
        resource_type="file",
        resource_id=filename,
        details={
            "original_name": file.filename,
            "size": file_size,
            "type": file_ext
        }
    )
    
    return {
        "success": True,
        "filename": filename,
        "original_name": file.filename,
        "size": file_size,
        "path": f"uploads/{filename}"
    }


@app.get("/api/uploads")
async def list_uploads(user: User = Depends(get_current_user)):
    """List user's uploaded files."""
    upload_dir = get_user_upload_dir(user.id)
    
    files = []
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "uploaded_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
    
    return {"files": sorted(files, key=lambda x: x["uploaded_at"], reverse=True)}


@app.delete("/api/uploads/{filename}")
async def delete_upload(filename: str, user: User = Depends(get_current_user)):
    """Delete an uploaded file."""
    upload_dir = get_user_upload_dir(user.id)
    file_path = upload_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check: ensure file is in user's upload directory
    try:
        file_path.resolve().relative_to(upload_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path.unlink()
    
    audit = get_audit_logger()
    audit.log(
        user_id=user.id,
        action="file_delete",
        resource_type="file",
        resource_id=filename
    )
    
    return {"success": True, "message": "File deleted"}


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenHarness Enterprise Server")
    parser.add_argument("command", choices=["start", "init"], help="Command to run")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    
    args = parser.parse_args()
    
    if args.command == "init":
        # Initialize database and create admin
        print("[*] Initializing OpenHarness Enterprise...")
        init_database()
        get_workspace_manager()
        _ensure_admin_user()
        print("[OK] Initialization complete!")
        return
    
    if args.command == "start":
        print(f"[*] Starting server on {args.host}:{args.port}")
        uvicorn.run(
            "openharness.enterprise.server:app",
            host=args.host,
            port=args.port,
            reload=False
        )


# ============================================================================
# Audit Logs API
# ============================================================================

@app.get("/api/admin/audit-logs")
async def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    admin: User = Depends(require_admin)
):
    """Get audit logs (admin only)."""
    db = get_database()
    
    logs = db.query_audit_logs(
        user_id=user_id,
        action=action,
        page=page,
        limit=limit
    )
    
    # Count total
    # Note: Simplified - in production you'd want a separate count query
    total = len(logs) if len(logs) < limit else page * limit + 1
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


# ============================================================================
# Static Files (Frontend)
# ============================================================================

# Get web directory path (web/dist for built frontend)
WEB_DIR = Path(__file__).parent.parent.parent.parent / "web" / "dist"

# Mount static files if web directory exists
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
    
    # Mount assets for frontend (CSS, JS)
    if (WEB_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")
    
    @app.get("/")
    async def root():
        """Redirect to web frontend."""
        return FileResponse(str(WEB_DIR / "index.html"))
    
    # SPA routes for frontend routing
    @app.get("/admin")
    async def admin_spa():
        """SPA route for admin panel."""
        return FileResponse(str(WEB_DIR / "index.html"))
    
    @app.get("/chat")
    async def chat_spa():
        """SPA route for chat."""
        return FileResponse(str(WEB_DIR / "index.html"))


if __name__ == "__main__":
    main()