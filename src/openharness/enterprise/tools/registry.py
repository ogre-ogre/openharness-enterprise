"""
OpenHarness Enterprise - Tools Registry

Tool definitions and management.
"""

from __future__ import annotations

import json
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from pydantic import BaseModel
from enum import Enum
import inspect

from openharness.enterprise.config.settings import get_settings


class ToolCategory(str, Enum):
    """Tool category."""
    FILE = "file"           # 文件操作
    WEB = "web"             # 网络操作
    SYSTEM = "system"       # 系统操作
    DATABASE = "database"   # 数据库操作
    CUSTOM = "custom"       # 自定义工具


class ToolPermission(str, Enum):
    """Tool permission level."""
    READ = "read"           # 只读操作
    WRITE = "write"         # 写入操作
    EXECUTE = "execute"     # 执行操作
    ADMIN = "admin"         # 管理员操作


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


class ToolDefinition(BaseModel):
    """Tool definition."""
    name: str
    description: str
    category: ToolCategory
    permission: ToolPermission
    parameters: Dict[str, ToolParameter]
    returns: str = "string"
    is_dangerous: bool = False
    is_enabled: bool = True
    timeout: int = 30  # seconds
    created_at: Optional[datetime] = None


class ToolResult(BaseModel):
    """Tool execution result."""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0


# ============================================================================
# Built-in Tools
# ============================================================================

BUILTIN_TOOLS = [
    # File Operations
    ToolDefinition(
        name="read_file",
        description="读取文件内容",
        category=ToolCategory.FILE,
        permission=ToolPermission.READ,
        parameters={
            "path": ToolParameter(
                type="string",
                description="文件路径（相对或绝对路径）",
                required=True
            ),
            "limit": ToolParameter(
                type="integer",
                description="最大读取行数",
                required=False,
                default=100
            )
        },
        created_at=datetime.utcnow()
    ),
    ToolDefinition(
        name="write_file",
        description="写入文件内容",
        category=ToolCategory.FILE,
        permission=ToolPermission.WRITE,
        parameters={
            "path": ToolParameter(
                type="string",
                description="文件路径",
                required=True
            ),
            "content": ToolParameter(
                type="string",
                description="文件内容",
                required=True
            )
        },
        is_dangerous=True,
        created_at=datetime.utcnow()
    ),
    ToolDefinition(
        name="edit_file",
        description="编辑文件（精确替换）",
        category=ToolCategory.FILE,
        permission=ToolPermission.WRITE,
        parameters={
            "path": ToolParameter(
                type="string",
                description="文件路径",
                required=True
            ),
            "old_text": ToolParameter(
                type="string",
                description="要替换的文本",
                required=True
            ),
            "new_text": ToolParameter(
                type="string",
                description="替换后的文本",
                required=True
            )
        },
        is_dangerous=True,
        created_at=datetime.utcnow()
    ),
    ToolDefinition(
        name="list_files",
        description="列出目录下的文件",
        category=ToolCategory.FILE,
        permission=ToolPermission.READ,
        parameters={
            "path": ToolParameter(
                type="string",
                description="目录路径",
                required=True
            ),
            "pattern": ToolParameter(
                type="string",
                description="文件匹配模式（如 *.py）",
                required=False
            )
        },
        created_at=datetime.utcnow()
    ),
    ToolDefinition(
        name="delete_file",
        description="删除文件",
        category=ToolCategory.FILE,
        permission=ToolPermission.WRITE,
        parameters={
            "path": ToolParameter(
                type="string",
                description="文件路径",
                required=True
            )
        },
        is_dangerous=True,
        created_at=datetime.utcnow()
    ),
    
    # Web Operations
    ToolDefinition(
        name="search_web",
        description="搜索网页",
        category=ToolCategory.WEB,
        permission=ToolPermission.READ,
        parameters={
            "query": ToolParameter(
                type="string",
                description="搜索关键词",
                required=True
            ),
            "count": ToolParameter(
                type="integer",
                description="返回结果数量",
                required=False,
                default=5
            )
        },
        created_at=datetime.utcnow()
    ),
    ToolDefinition(
        name="fetch_url",
        description="获取网页内容",
        category=ToolCategory.WEB,
        permission=ToolPermission.READ,
        parameters={
            "url": ToolParameter(
                type="string",
                description="网页 URL",
                required=True
            )
        },
        created_at=datetime.utcnow()
    ),
    
    # System Operations
    ToolDefinition(
        name="execute_command",
        description="执行系统命令",
        category=ToolCategory.SYSTEM,
        permission=ToolPermission.EXECUTE,
        parameters={
            "command": ToolParameter(
                type="string",
                description="要执行的命令",
                required=True
            ),
            "timeout": ToolParameter(
                type="integer",
                description="超时时间（秒）",
                required=False,
                default=30
            )
        },
        is_dangerous=True,
        timeout=60,
        created_at=datetime.utcnow()
    ),
    
    # Database Operations
    ToolDefinition(
        name="query_database",
        description="执行数据库查询",
        category=ToolCategory.DATABASE,
        permission=ToolPermission.READ,
        parameters={
            "sql": ToolParameter(
                type="string",
                description="SQL 查询语句",
                required=True
            )
        },
        created_at=datetime.utcnow()
    ),
    
    # REST API Operations
    ToolDefinition(
        name="rest_api_call",
        description="执行 REST API 调用，支持 GET/POST/PUT/DELETE 方法。自动从环境变量获取认证 Token 并添加到请求头。",
        category=ToolCategory.WEB,
        permission=ToolPermission.EXECUTE,
        parameters={
            "url": ToolParameter(
                type="string",
                description="完整的 API URL",
                required=True
            ),
            "method": ToolParameter(
                type="string",
                description="HTTP 方法：GET、POST、PUT、DELETE",
                required=True,
                enum=["GET", "POST", "PUT", "DELETE"]
            ),
            "headers": ToolParameter(
                type="object",
                description="额外的请求头（会自动添加 Authorization 和 Content-Type）",
                required=False
            ),
            "query_params": ToolParameter(
                type="object",
                description="URL 查询参数（对象格式，会被自动编码）",
                required=False
            ),
            "body": ToolParameter(
                type="string",
                description="请求体（JSON 字符串，仅 POST/PUT 需要时使用）",
                required=False
            ),
            "token_env_var": ToolParameter(
                type="string",
                description="存储认证 Token 的环境变量名（默认：REST_API_TOKEN）",
                required=False,
                default="REST_API_TOKEN"
            ),
        },
        created_at=datetime.utcnow()
    ),
]


# ============================================================================
# Tool Executor
# ============================================================================

class ToolExecutor:
    """
    Executes tool calls.
    
    Handles:
    - File operations
    - Web operations
    - System commands
    - Custom tools
    """
    
    # Allowed directories for file operations (security whitelist)
    ALLOWED_PATHS = [
        Path.home() / ".oh-enterprise",      # Data directory
        Path.home() / ".oh-enterprise" / "shared",  # Shared resources
        Path.home() / ".oh-enterprise" / "users",   # User uploads
    ]
    
    # Blocked path patterns (security)
    BLOCKED_PATTERNS = [
        "..",           # Path traversal
        "~",            # Home directory (except allowed paths)
        "/etc",         # System config
        "/root",        # Root home
        ".ssh",         # SSH keys
        ".env",         # Environment files
        "id_rsa",       # Private keys
        ".gitconfig",   # Git config
    ]
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or (Path.home() / ".oh-enterprise")
        
        # Add workspace to allowed paths
        if self.workspace_path not in self.ALLOWED_PATHS:
            self.ALLOWED_PATHS.insert(0, self.workspace_path)
        
        self._handlers: Dict[str, Callable] = {}
        self._current_user_id: Optional[int] = None
        self._downloads_path: Optional[str] = None  # [新增] 用户下载路径
        
        # Register built-in handlers
        self._register_builtin_handlers()
    
    def set_user_id(self, user_id: Optional[int]) -> None:
        """Set the current user ID for permission checks."""
        self._current_user_id = user_id
    
    def set_downloads_path(self, downloads_path: Optional[str]) -> None:
        """[新增] Set the user's downloads path for environment injection."""
        self._downloads_path = downloads_path
    
    def _register_builtin_handlers(self) -> None:
        """Register built-in tool handlers."""
        self._handlers = {
            "read_file": self._read_file,
            "write_file": self._write_file,
            "edit_file": self._edit_file,
            "list_files": self._list_files,
            "delete_file": self._delete_file,
            "search_web": self._search_web,
            "fetch_url": self._fetch_url,
            "execute_command": self._execute_command,
            "query_database": self._query_database,
            "rest_api_call": self._rest_api_call,
        }
    
    def get_handler(self, tool_name: str) -> Optional[Callable]:
        """Get tool handler by name."""
        return self._handlers.get(tool_name)
    
    def register_handler(self, tool_name: str, handler: Callable) -> None:
        """Register custom tool handler."""
        self._handlers[tool_name] = handler
    
    def execute(self, tool_name: str, parameters: Dict[str, Any], user_id: Optional[int] = None) -> ToolResult:
        """
        Execute a tool.
        
        Args:
            tool_name: Tool name
            parameters: Tool parameters
            user_id: User ID for permission checks
        
        Returns:
            ToolResult
        """
        import time
        start_time = time.time()
        
        # Set user ID for permission checks
        self._current_user_id = user_id
        
        handler = self._handlers.get(tool_name)
        if not handler:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{tool_name}' not found"
            )
        
        try:
            result = handler(**parameters)
            
            # [新增] 如果是 execute_command，附加环境变量提示
            if tool_name == "execute_command" and isinstance(result, dict):
                # 构建环境变量提示信息
                env_hint = ""
                if self._downloads_path:
                    env_hint = f"\n\n📌 可用的环境变量:\n- OH_DOWNLOADS_PATH={self._downloads_path}\n- OH_USER_ID={self._current_user_id or 'unknown'}\n\n请使用 os.environ.get('OH_DOWNLOADS_PATH') 获取文件保存路径！"
                    if "stdout" in result:
                        result["stdout"] = result["stdout"] + env_hint
                    elif "output" in result:
                        result["output"] = str(result["output"]) + env_hint
            
            return ToolResult(
                success=True,
                output=result,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    # ========================================================================
    # File Operations
    # ========================================================================
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to workspace with security checks."""
        p = Path(path)
        
        # Security check: Block path traversal
        if ".." in path:
            raise PermissionError("Path traversal not allowed: '..' detected")
        
        # Security check: Block absolute paths outside allowed directories
        if p.is_absolute():
            if not self._is_path_allowed(p):
                raise PermissionError(f"Access denied: {path} is outside allowed directories")
            return p
        
        # Handle paths starting with .oh-enterprise specially
        # These should resolve to ~/.oh-enterprise/... directly
        path_normalized = path.replace('\\', '/')
        if path_normalized.startswith('.oh-enterprise/'):
            # Remove the .oh-enterprise/ prefix and resolve from home
            sub_path = path_normalized[len('.oh-enterprise/'):]  # len = 15
            resolved = (Path.home() / '.oh-enterprise' / sub_path).resolve()
        elif path_normalized.startswith('.oh-enterprise\\'):
            sub_path = path_normalized[len('.oh-enterprise\\'):]
            resolved = (Path.home() / '.oh-enterprise' / sub_path).resolve()
        else:
            # Resolve relative path from workspace
            resolved = (self.workspace_path / path).resolve()
        
        # Security check: Ensure resolved path is within allowed directories
        if not self._is_path_allowed(resolved):
            raise PermissionError(f"Access denied: {path} resolves outside allowed directories")
        
        # Security check: User directory isolation
        if not self._check_user_directory_access(resolved):
            raise PermissionError(f"Access denied: {path} is not in your user directory")
        
        return resolved
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is in allowed directories."""
        try:
            resolved = path.resolve()
            
            # Check if path is within any allowed directory
            for allowed in self.ALLOWED_PATHS:
                try:
                    resolved.relative_to(allowed.resolve())
                    return True
                except ValueError:
                    continue
            
            return False
        except Exception:
            return False
    
    def _check_user_directory_access(self, path: Path) -> bool:
        """
        Check if user has access to the path.
        
        Rules:
        - If path is under users/{user_id}/, only the owner can access
        - If path is under shared/, everyone can access
        - Other paths require the path to contain user's own user_id
        """
        if self._current_user_id is None:
            # No user context, allow access (backward compatibility)
            return True
        
        try:
            resolved = path.resolve()
            path_str = str(resolved)
            
            # Check if path is under users directory
            users_dir = (Path.home() / '.oh-enterprise' / 'users').resolve()
            shared_dir = (Path.home() / '.oh-enterprise' / 'shared').resolve()
            
            # Shared directory is accessible to all
            try:
                resolved.relative_to(shared_dir)
                return True
            except ValueError:
                pass
            
            # Check if path is under users directory
            try:
                relative = resolved.relative_to(users_dir)
                # Path is under users/, check if it's user's own directory
                # Format: users/{user_id}/...
                parts = relative.parts
                if len(parts) >= 1:
                    # First part should be the user_id
                    try:
                        path_user_id = int(parts[0])
                        # Only allow access to own directory
                        return path_user_id == self._current_user_id
                    except ValueError:
                        # Not a numeric user_id, deny access
                        return False
            except ValueError:
                pass
            
            # Path is not under users or shared, check general allowed paths
            # This allows access to other directories like workspace root
            return True
            
        except Exception:
            return False
    
    def _check_blocked_patterns(self, path: str) -> None:
        """Check for blocked path patterns."""
        path_lower = path.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.lower() in path_lower:
                raise PermissionError(f"Access denied: blocked pattern '{pattern}' in path")
    
    def _read_file(self, path: str, limit: int = 100) -> str:
        """Read file content with auto-detection of encoding."""
        # Security checks
        self._check_blocked_patterns(path)
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Not a file: {path}")
        
        # Try different encodings
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16', 'latin-1']
        content = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                content = lines
                used_encoding = encoding
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if content is None:
            raise ValueError(f"Unable to decode file with supported encodings: {path}")
        
        if len(content) > limit:
            return ''.join(content[:limit]) + f"\n... (truncated, {len(content)} total lines)"
        
        return ''.join(content)
    
    def _write_file(self, path: str, content: str) -> str:
        """Write file content."""
        # Security checks
        self._check_blocked_patterns(path)
        file_path = self._resolve_path(path)
        
        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"File written: {path} ({len(content)} characters)"
    
    def _edit_file(self, path: str, old_text: str, new_text: str) -> str:
        """Edit file by replacing text."""
        # Security checks
        self._check_blocked_patterns(path)
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        content = file_path.read_text(encoding='utf-8')
        
        if old_text not in content:
            raise ValueError(f"Text not found in file: {old_text[:50]}...")
        
        new_content = content.replace(old_text, new_text)
        file_path.write_text(new_content, encoding='utf-8')
        
        return f"File edited: {path}"
    
    def _list_files(self, path: str, pattern: str = None) -> List[str]:
        """List files in directory."""
        # Security checks
        self._check_blocked_patterns(path)
        dir_path = self._resolve_path(path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {path}")
        
        if pattern:
            files = list(dir_path.glob(pattern))
        else:
            files = list(dir_path.iterdir())
        
        return [
            {
                "name": f.name,
                "type": "directory" if f.is_dir() else "file",
                "size": f.stat().st_size if f.is_file() else None
            }
            for f in sorted(files)
        ]
    
    def _delete_file(self, path: str) -> str:
        """Delete file."""
        # Security checks
        self._check_blocked_patterns(path)
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if file_path.is_dir():
            shutil.rmtree(file_path)
            return f"Directory deleted: {path}"
        else:
            file_path.unlink()
            return f"File deleted: {path}"
    
    # ========================================================================
    # Web Operations
    # ========================================================================
    
    def _search_web(self, query: str, count: int = 5) -> List[Dict]:
        """Search web (mock implementation)."""
        # TODO: Implement real web search
        return [
            {
                "title": f"Search result {i+1} for: {query}",
                "url": f"https://example.com/result/{i+1}",
                "snippet": f"This is a mock search result for '{query}'..."
            }
            for i in range(count)
        ]
    
    def _fetch_url(self, url: str) -> str:
        """Fetch URL content."""
        import urllib.request
        
        try:
            timeout = get_settings().tool_timeout
            with urllib.request.urlopen(url, timeout=timeout) as response:
                content = response.read().decode('utf-8')
                # Truncate large responses
                if len(content) > 10000:
                    content = content[:10000] + "\n... (truncated)"
                return content
        except Exception as e:
            raise RuntimeError(f"Failed to fetch URL: {e}")
    
    # ========================================================================
    # System Operations
    # ========================================================================
    
    def _execute_command(self, command: str, timeout: int = 30) -> Dict:
        """Execute system command with user context environment variables."""
        # [新增] 构建环境变量
        env = os.environ.copy()
        
        # 注入用户上下文环境变量
        if self._current_user_id is not None:
            env["OH_USER_ID"] = str(self._current_user_id)
            
            # 用户工作区路径
            user_workspace = Path.home() / ".oh-enterprise" / "users" / str(self._current_user_id)
            env["OH_WORKSPACE_PATH"] = str(user_workspace)
        
        # 注入下载路径
        if self._downloads_path:
            env["OH_DOWNLOADS_PATH"] = self._downloads_path
            # 确保目录存在
            Path(self._downloads_path).mkdir(parents=True, exist_ok=True)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace_path),
                env=env  # [新增] 传递环境变量
            )
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "downloads_path": self._downloads_path  # [新增] 返回下载路径信息
            }
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {e}")
    
    # ========================================================================
    # Database Operations
    # ========================================================================
    
    def _query_database(self, sql: str) -> List[Dict]:
        """Execute database query."""
        # TODO: Implement with actual database connection
        raise NotImplementedError("Database query not implemented")
    
    # ========================================================================
    # REST API Operations
    # ========================================================================
    
    def _rest_api_call(
        self,
        url: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        token_env_var: str = "REST_API_TOKEN"
    ) -> Dict:
        """
        Execute REST API call.
        
        Args:
            url: Complete API URL
            method: HTTP method (GET/POST/PUT/DELETE)
            headers: Additional request headers
            query_params: URL query parameters
            body: Request body (JSON string for POST/PUT)
            token_env_var: Environment variable name for auth token
        
        Returns:
            Dict with success, status, and data
        """
        import urllib.request
        import urllib.parse
        import urllib.error
        
        # Build URL with query parameters
        if query_params:
            parsed_url = urllib.parse.urlparse(url)
            existing_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Merge with existing params
            for key, value in query_params.items():
                existing_params[key] = [value]
            
            # Rebuild query string
            new_query = urllib.parse.urlencode(existing_params, doseq=True)
            url = urllib.parse.urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                 parsed_url.params, new_query, parsed_url.fragment)
            )
        
        # Build request headers
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Get auth token from environment variable
        auth_token = os.environ.get(token_env_var, "")
        if auth_token:
            request_headers["Authorization"] = f"Bearer {auth_token}"
        
        # Merge additional headers
        if headers:
            request_headers.update(headers)
        
        # Prepare request body
        data = None
        if method in ["POST", "PUT"] and body:
            data = body.encode("utf-8")
        
        try:
            # Create request
            req = urllib.request.Request(
                url,
                data=data,
                headers=request_headers,
                method=method
            )
            
            # Execute request
            timeout = get_settings().tool_timeout
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_body = response.read().decode("utf-8")
                
                # Try to parse JSON response
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    try:
                        response_data = json.loads(response_body)
                    except json.JSONDecodeError:
                        response_data = response_body
                else:
                    response_data = response_body
                
                return {
                    "success": True,
                    "status": response.status,
                    "status_text": response.reason,
                    "headers": dict(response.headers),
                    "data": response_data
                }
        
        except urllib.error.HTTPError as e:
            # Handle HTTP errors
            try:
                error_body = e.read().decode("utf-8")
                try:
                    error_data = json.loads(error_body)
                except json.JSONDecodeError:
                    error_data = error_body
            except Exception:
                error_data = None
            
            return {
                "success": False,
                "status": e.code,
                "status_text": e.reason,
                "error": error_data
            }
        
        except urllib.error.URLError as e:
            return {
                "success": False,
                "error": f"URL Error: {e.reason}"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }


# ============================================================================
# Tool Registry
# ============================================================================

class ToolRegistry:
    """
    Tool registry and management.
    
    Features:
    - List available tools
    - Get tool definitions
    - Execute tools
    - Custom tool registration
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or (Path.home() / ".oh-enterprise" / "tools")
        self.tools: Dict[str, ToolDefinition] = {}
        self.executor = ToolExecutor()
        
        # Ensure directory exists
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Load tools
        self._load_tools()
    
    def _load_tools(self) -> None:
        """Load tool definitions."""
        # Load built-in tools
        for tool in BUILTIN_TOOLS:
            self.tools[tool.name] = tool
        
        # Load custom tools from file
        custom_tools_file = self.data_path / "custom_tools.json"
        if custom_tools_file.exists():
            try:
                data = json.loads(custom_tools_file.read_text(encoding="utf-8"))
                for tool_data in data:
                    tool = ToolDefinition(**tool_data)
                    self.tools[tool.name] = tool
            except Exception:
                pass
    
    def _save_custom_tools(self) -> None:
        """Save custom tools to file."""
        custom_tools_file = self.data_path / "custom_tools.json"
        
        custom_tools = [
            tool.dict()
            for tool in self.tools.values()
            if tool.category == ToolCategory.CUSTOM
        ]
        
        custom_tools_file.write_text(
            json.dumps(custom_tools, indent=2, default=str),
            encoding="utf-8"
        )
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """List all available tools."""
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t.category.value == category]
        
        return tools
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name."""
        return self.tools.get(name)
    
    def get_tool_schema(self, name: str) -> Optional[Dict]:
        """Get tool schema in OpenAI format."""
        tool = self.tools.get(name)
        if not tool:
            return None
        
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        name: {
                            "type": param.type,
                            "description": param.description
                        }
                        for name, param in tool.parameters.items()
                    },
                    "required": [
                        name for name, param in tool.parameters.items()
                        if param.required
                    ]
                }
            }
        }
    
    def get_all_schemas(self) -> List[Dict]:
        """Get all tool schemas for LLM."""
        return [
            self.get_tool_schema(name)
            for name, tool in self.tools.items()
            if tool.is_enabled
        ]
    
    def execute_tool(self, name: str, parameters: Dict[str, Any], user_id: Optional[int] = None, downloads_path: Optional[str] = None) -> ToolResult:
        """Execute a tool with optional user context for permission checks."""
        tool = self.tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{name}' not found"
            )
        
        if not tool.is_enabled:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{name}' is disabled"
            )
        
        # [新增] 设置用户下载路径
        self.executor.set_downloads_path(downloads_path)
        
        return self.executor.execute(name, parameters, user_id=user_id)
    
    def register_custom_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Dict],
        handler: Optional[Callable] = None
    ) -> ToolDefinition:
        """Register a custom tool."""
        tool = ToolDefinition(
            name=name,
            description=description,
            category=ToolCategory.CUSTOM,
            permission=ToolPermission.EXECUTE,
            parameters={
                k: ToolParameter(**v) for k, v in parameters.items()
            },
            created_at=datetime.utcnow()
        )
        
        self.tools[name] = tool
        
        if handler:
            self.executor.register_handler(name, handler)
        
        self._save_custom_tools()
        
        return tool
    
    def update_tool(self, name: str, is_enabled: Optional[bool] = None) -> Optional[ToolDefinition]:
        """Update tool settings."""
        tool = self.tools.get(name)
        if not tool:
            return None
        
        if is_enabled is not None:
            tool.is_enabled = is_enabled
        
        self._save_custom_tools()
        return tool


# Singleton
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry