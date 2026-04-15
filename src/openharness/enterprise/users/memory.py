"""
OpenHarness Enterprise - Memory Manager

Manages user memory files:
- MEMORY.md - Long-term curated memory
- YYYY-MM-DD.md - Daily memory logs
"""

from __future__ import annotations

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

from openharness.enterprise.users.workspace import get_user_workspace_path


class MemoryManager:
    """
    User memory manager.
    
    Features:
    - Read/write MEMORY.md (long-term memory)
    - Read/write daily memory files
    - Append significant events
    - Memory consolidation
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.memory_path = get_user_workspace_path(user_id) / "memory"
        
        # Ensure memory directory exists
        self.memory_path.mkdir(parents=True, exist_ok=True)
    
    # ------------------------------------------------------------------------
    # Read Operations
    # ------------------------------------------------------------------------
    
    def get_memory_file(self) -> Path:
        """Get MEMORY.md path."""
        return self.memory_path / "MEMORY.md"
    
    def get_daily_file(self, date_str: Optional[str] = None) -> Path:
        """Get daily memory file path."""
        if not date_str:
            date_str = date.today().isoformat()
        return self.memory_path / f"{date_str}.md"
    
    def read_memory(self) -> str:
        """Read long-term memory content."""
        memory_file = self.get_memory_file()
        if memory_file.exists():
            return memory_file.read_text(encoding="utf-8")
        return ""
    
    def read_daily(self, date_str: Optional[str] = None) -> str:
        """Read daily memory content."""
        daily_file = self.get_daily_file(date_str)
        if daily_file.exists():
            return daily_file.read_text(encoding="utf-8")
        return ""
    
    def read_all_daily(self, limit: int = 7) -> List[Dict[str, Any]]:
        """Read recent daily memory files."""
        daily_files = []
        for f in sorted(self.memory_path.glob("*.md"), reverse=True):
            if f.name != "MEMORY.md":
                daily_files.append({
                    "date": f.stem,
                    "content": f.read_text(encoding="utf-8")
                })
        return daily_files[:limit]
    
    # ------------------------------------------------------------------------
    # Write Operations
    # ------------------------------------------------------------------------
    
    def write_memory(self, content: str) -> None:
        """Write/overwrite long-term memory."""
        memory_file = self.get_memory_file()
        memory_file.write_text(content, encoding="utf-8")
    
    def append_to_memory(self, section: str, content: str) -> None:
        """
        Append a section to long-term memory.
        
        Args:
            section: Section title (e.g., "项目信息", "学到的教训")
            content: Content to append
        """
        memory_file = self.get_memory_file()
        
        existing_content = ""
        if memory_file.exists():
            existing_content = memory_file.read_text(encoding="utf-8")
        
        # Check if section already exists
        section_marker = f"\n## {section}\n"
        
        if section_marker in existing_content:
            # Append to existing section
            # Find the section and add content before next section
            lines = existing_content.split("\n")
            new_lines = []
            in_section = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                
                if line.strip() == f"## {section}":
                    in_section = True
                elif in_section and line.startswith("## ") and line.strip() != f"## {section}":
                    # End of section, insert before next section
                    new_lines.append(f"\n{content}\n")
                    in_section = False
            
            if in_section:
                # Section was last, append at end
                new_lines.append(f"\n{content}\n")
            
            new_content = "\n".join(new_lines)
        else:
            # New section
            new_content = existing_content + f"\n\n## {section}\n\n{content}\n"
        
        memory_file.write_text(new_content, encoding="utf-8")
    
    def write_daily(self, content: str, date_str: Optional[str] = None) -> None:
        """Write/overwrite daily memory."""
        daily_file = self.get_daily_file(date_str)
        daily_file.write_text(content, encoding="utf-8")
    
    def append_to_daily(self, event: str, date_str: Optional[str] = None) -> None:
        """
        Append an event to daily memory.
        
        Args:
            event: Event description
            date_str: Date string (defaults to today)
        """
        daily_file = self.get_daily_file(date_str)
        
        existing_content = ""
        if daily_file.exists():
            existing_content = daily_file.read_text(encoding="utf-8")
        
        # Format event with timestamp
        timestamp = datetime.now().strftime("%H:%M")
        event_line = f"- [{timestamp}] {event}\n"
        
        # If file is empty, add header
        if not existing_content.strip():
            date_label = date_str or date.today().isoformat()
            header = f"# {date_label} - 日常记录\n\n## 事件\n\n"
            new_content = header + event_line
        else:
            # Append to events section
            if "## 事件" in existing_content:
                # Find events section and append
                lines = existing_content.split("\n")
                new_lines = []
                in_events = False
                inserted = False
                
                for line in lines:
                    new_lines.append(line)
                    
                    if line.strip() == "## 事件":
                        in_events = True
                    elif in_events and line.startswith("## ") and not inserted:
                        # Next section, insert before
                        new_lines.append(event_line)
                        inserted = True
                        in_events = False
                
                if in_events and not inserted:
                    new_lines.append(event_line)
                
                new_content = "\n".join(new_lines)
            else:
                # No events section, create it
                new_content = existing_content + f"\n\n## 事件\n\n{event_line}"
        
        daily_file.write_text(new_content, encoding="utf-8")
    
    # ------------------------------------------------------------------------
    # Memory Consolidation
    # ------------------------------------------------------------------------
    
    def consolidate_daily_to_memory(self) -> None:
        """
        Consolidate recent daily memories into long-term memory.
        
        This is a manual process - AI should identify significant events
        from daily files and add them to MEMORY.md.
        """
        recent_daily = self.read_all_daily(limit=7)
        
        if not recent_daily:
            return
        
        # Extract significant events
        events = []
        for daily in recent_daily:
            content = daily["content"]
            # Look for significant markers (could be customized)
            for line in content.split("\n"):
                if "重要" in line or "决策" in line or "教训" in line or "记住" in line:
                    events.append(f"- [{daily['date']}] {line}")
        
        if events:
            self.append_to_memory(
                "最近重要事件",
                "\n".join(events)
            )
    
    # ------------------------------------------------------------------------
    # Memory Context Builder
    # ------------------------------------------------------------------------
    
    def build_memory_context(self, include_daily: bool = True) -> str:
        """
        Build memory context for LLM.
        
        Args:
            include_daily: Whether to include recent daily memories
        
        Returns:
            Memory context string
        """
        parts = []
        
        # Long-term memory
        long_term = self.read_memory()
        if long_term.strip():
            parts.append("## 长期记忆\n\n" + long_term)
        
        # Recent daily memories
        if include_daily:
            daily_memories = self.read_all_daily(limit=3)
            if daily_memories:
                daily_parts = []
                for daily in daily_memories:
                    content = daily["content"]
                    # Extract key events
                    events = []
                    for line in content.split("\n"):
                        if line.startswith("- ["):
                            events.append(line)
                    if events:
                        daily_parts.append(f"### {daily['date']}\n" + "\n".join(events[:5]))
                
                if daily_parts:
                    parts.append("## 最近记忆\n\n" + "\n\n".join(daily_parts))
        
        return "\n\n".join(parts) if parts else ""


# ============================================================================
# Factory Function
# ============================================================================

def get_memory_manager(user_id: int) -> MemoryManager:
    """Get memory manager for user."""
    return MemoryManager(user_id)