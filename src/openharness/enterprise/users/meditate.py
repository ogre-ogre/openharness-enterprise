"""
OpenHarness Enterprise - Meditate Mechanism

每日反思机制 - 知识提取、外置、重组织
"""

from __future__ import annotations

import json
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta

from openharness.enterprise.storage.database import get_database
from openharness.enterprise.users.workspace import get_user_workspace_path
from openharness.enterprise.users.memory import get_memory_manager
from openharness.enterprise.llm.client import get_llm_client
from openharness.enterprise.config.settings import get_settings


class MeditateExecutor:
    """
    每日记忆反思执行器
    
    功能：
    1. 收集昨日对话
    2. AI 分析提取关键信息
    3. 长内容外置到知识文件
    4. 重组织 MEMORY.md
    """
    
    # 使用配置管理替代硬编码
    KNOWLEDGE_DIR = "knowledge"
    
    def __init__(self, user_id: int):
        if user_id is None or user_id <= 0:
            raise ValueError("user_id is required for MeditateExecutor")
        
        self.user_id = user_id
        self.db = get_database()
        self.workspace = get_user_workspace_path(user_id)
        self.memory_mgr = get_memory_manager(user_id)
        self.knowledge_dir = self.workspace / self.KNOWLEDGE_DIR
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # 从配置获取阈值
        self._settings = get_settings()
    
    @property
    def knowledge_threshold(self) -> int:
        """知识外置阈值（从配置获取）"""
        return self._settings.knowledge_threshold
    
    async def execute_async(self, date: Optional[str] = None) -> Dict[str, Any]:
        """执行每日 Meditate（async 版本）"""
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        conversations = self._collect_conversations(date)
        
        if not conversations:
            return {"status": "skipped", "reason": "no_conversations", "date": date}
        
        extracted = await self._extract_knowledge_async(conversations)
        externalized = self._externalize_knowledge(extracted.get("long_content", []))
        self._merge_to_memory(extracted, externalized)
        await self._reorganize_memory_async()
        
        return {
            "status": "success",
            "date": date,
            "conversations_count": len(conversations),
            "extracted": {
                "operations": len(extracted.get("operations", [])),
                "knowledge": len(extracted.get("knowledge", [])),
                "notes": len(extracted.get("notes", []))
            },
            "knowledge_externalized": len(externalized)
        }
    
    def _collect_conversations(self, date: str) -> Dict:
        """收集指定日期的对话"""
        cursor = self.db._conn.cursor()
        cursor.execute("""
            SELECT m.id, m.session_id, m.role, m.content, m.created_at
            FROM messages m
            JOIN sessions s ON m.session_id = s.id
            WHERE s.user_id = ?
            AND date(m.created_at) = ?
            ORDER BY m.created_at
        """, (self.user_id, date))
        
        rows = cursor.fetchall()
        
        sessions = {}
        for row in rows:
            session_id = row[1]
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append({
                "role": row[2],
                "content": row[3],
                "created_at": row[4]
            })
        
        return sessions
    
    async def _extract_knowledge_async(self, conversations: Dict) -> Dict[str, Any]:
        """使用 AI 分析对话，提取关键信息"""
        all_content = self._build_conversation_summary(conversations)
        
        if not all_content:
            return {"operations": [], "knowledge": [], "notes": [], "long_content": []}
        
        analysis_prompt = f"""请分析以下对话记录，提取需要记忆的重要信息：

{all_content}

请按以下格式返回 JSON：
{{{{
    "operations": [
        {{{{ "title": "操作名称", "steps": ["步骤1", "步骤2"], "context": "应用场景" }}}}
    ],
    "knowledge": [
        {{{{ "topic": "知识点主题", "summary": "核心要点（不超过100字）", "details": "详细说明" }}}}
    ],
    "notes": [
        {{{{ "content": "备忘内容", "priority": "high/medium/low" }}}}
    ],
    "long_content": [
        {{{{ "title": "主题", "content": "具体内容（超过2000字的内容单独列出）" }}}}
    ]
}}}}

只返回 JSON，不要其他内容。如果没有重要信息，返回空数组。"""

        llm_client = get_llm_client()
        messages = [{"role": "user", "content": analysis_prompt}]
        
        result = ""
        try:
            async for chunk in llm_client.stream_chat(
                messages=messages,
                system_prompt="你是一个记忆分析助手，专门从对话中提取需要长期保存的信息。只返回JSON格式。"
            ):
                result += chunk
            print(f"[Meditate] LLM response: {result[:200]}...")
        except Exception as e:
            print(f"[Meditate] LLM call failed: {e}")
            return {"operations": [], "knowledge": [], "notes": [], "long_content": []}
        
        try:
            start = result.find('{')
            end = result.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(result[start:end])
        except json.JSONDecodeError as e:
            print(f"[Meditate] JSON parse error: {e}")
        
        return {"operations": [], "knowledge": [], "notes": [], "long_content": []}
    
    def _build_conversation_summary(self, conversations: Dict) -> str:
        """构建对话摘要"""
        summary_parts = []
        
        for session_id, messages in conversations.items():
            for msg in messages:
                content = msg.get("content", "") or ""
                if len(content) > 500:
                    content = content[:500] + "..."
                role = msg.get("role", "user")
                summary_parts.append(f"[{role}]: {content}")
        
        return "\n\n".join(summary_parts[:50])
    
    def _externalize_knowledge(self, long_contents: List[Dict]) -> List[Dict]:
        """将长内容外置到单独的知识文件"""
        externalized = []
        
        for item in long_contents:
            content = item.get("content", "")
            if len(content) < self.knowledge_threshold:
                continue
            
            file_id = str(uuid.uuid4())[:8]
            title = item.get("title", "未命名")
            safe_title = "".join(c for c in title if c.isalnum() or c in "-_")[:30]
            filename = f"{safe_title}_{file_id}.md"
            
            file_path = self.knowledge_dir / filename
            file_path.write_text(f"# {title}\n\n{content}", encoding="utf-8")
            
            summary = content[:200] + "..." if len(content) > 200 else content
            
            externalized.append({
                "title": title,
                "path": str(file_path.relative_to(self.workspace)),
                "summary": summary
            })
        
        return externalized
    
    def _merge_to_memory(self, extracted: Dict, externalized: List[Dict]) -> None:
        """将提取的信息合并到 MEMORY.md"""
        
        for op in extracted.get("operations", []):
            content = f"### {op.get('title', '操作')}\n"
            content += f"应用场景：{op.get('context', 'N/A')}\n"
            content += "步骤：\n"
            for i, step in enumerate(op.get("steps", []), 1):
                content += f"{i}. {step}\n"
            self.memory_mgr.append_to_memory("操作记录", content)
        
        for kw in extracted.get("knowledge", []):
            topic = kw.get("topic", "知识")
            summary = kw.get("summary", "")
            details = kw.get("details", "")
            
            if len(details) < self.knowledge_threshold:
                content = f"**{topic}**: {summary}\n\n{details}"
                self.memory_mgr.append_to_memory("知识库", content)
            else:
                file_id = str(uuid.uuid4())[:8]
                safe_topic = "".join(c for c in topic if c.isalnum() or c in "-_")[:30]
                filename = f"{safe_topic}_{file_id}.md"
                
                (self.knowledge_dir / filename).write_text(
                    f"# {topic}\n\n{details}", 
                    encoding="utf-8"
                )
                
                ref = f"**{topic}**: {summary}\n\n[详细内容](./{self.KNOWLEDGE_DIR}/{filename})"
                self.memory_mgr.append_to_memory("知识库", ref)
        
        for note in extracted.get("notes", []):
            if note.get("priority") == "high":
                self.memory_mgr.append_to_memory("重要备忘", f"- {note.get('content', '')}")
        
        for ext in externalized:
            ref = f"- **{ext['title']}**: {ext['summary']}\n  [查看详情](./{ext['path']})"
            self.memory_mgr.append_to_memory("知识文件", ref)
    
    async def _reorganize_memory_async(self) -> None:
        """重组织 MEMORY.md"""
        current_content = self.memory_mgr.read_memory()
        
        if not current_content or len(current_content) < 500:
            return
        
        reorganization_prompt = f"""请重新组织以下记忆文件，使其更简洁、有条理：

要求：
1. 合并重复内容
2. 删除过时信息（超过30天的临时备忘）
3. 按主题分类整理
4. 保持每个知识点简洁（不超过100字）
5. 对于已经很长的内容，保留摘要

当前记忆内容：
{current_content[:3000]}

请返回重构后的记忆内容（保持 markdown 格式）："""

        llm_client = get_llm_client()
        messages = [{"role": "user", "content": reorganization_prompt}]
        
        result = ""
        try:
            async for chunk in llm_client.stream_chat(
                messages=messages,
                system_prompt="你是一个记忆整理助手，帮助用户整理和精简记忆。只返回整理后的内容。"
            ):
                result += chunk
            
            if result.strip() and len(result) < len(current_content) * 1.2:
                self.memory_mgr.write_memory(result)
                print(f"[Meditate] Memory reorganized: {len(current_content)} -> {len(result)} chars")
        except Exception as e:
            print(f"[Meditate] Reorganization failed: {e}")


class MeditateScheduler:
    """Meditate 定时调度器"""
    
    def __init__(self):
        self.db = get_database()
    
    async def run_daily_async(self) -> Dict[str, Any]:
        """每日执行（async 版本）"""
        results = {}
        
        users = self.db.get_all_users()
        
        for user in users:
            if not user.is_active:
                continue
            
            try:
                executor = MeditateExecutor(user.id)
                result = await executor.execute_async()
                results[user.id] = result
                print(f"[Meditate] User {user.id}: {result['status']}")
            except Exception as e:
                results[user.id] = {"status": "error", "message": str(e)}
                print(f"[Meditate] User {user.id} error: {e}")
        
        return results


def get_meditate_executor(user_id: int) -> MeditateExecutor:
    """获取 Meditate 执行器"""
    return MeditateExecutor(user_id)

def get_meditate_scheduler() -> MeditateScheduler:
    """获取 Meditate 调度器"""
    return MeditateScheduler()