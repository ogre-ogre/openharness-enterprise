"""
端到端测试工具调用
"""
import sys
sys.path.insert(0, r'src')

from dotenv import load_dotenv
load_dotenv('.env')

import asyncio
from openharness.enterprise.channels.webchat import AgentEngineInterface, ServerMessage
from openharness.enterprise.users.context import UserContext

# 创建一个简单的 UserContext
class SimpleUserContext:
    def __init__(self):
        self.soul = "你是一个有帮助的AI助手。"
        self.available_skills = []
        self.skills_path = None

async def test_tool_call():
    engine = AgentEngineInterface()
    
    message = "请读取 .oh-enterprise/users/1/uploads/ 目录下的文件"
    user_context = SimpleUserContext()
    conversation_history = []
    session_id = "test-session"
    
    print("=== Testing AgentEngineInterface ===")
    print(f"Message: {message}")
    print()
    
    full_response = ""
    async for server_msg in engine.run_stream(message, user_context, conversation_history, session_id):
        print(f"[{server_msg.type}] ", end="")
        if server_msg.type == "text":
            chunk = server_msg.payload.get("content", "")
            print(chunk, end="", flush=True)
            full_response += chunk
        elif server_msg.type == "tool_call":
            print(f"\nTool: {server_msg.payload.get('tool')}")
            print(f"Params: {server_msg.payload.get('params')}")
            print(f"Success: {server_msg.payload.get('result', {}).get('success')}")
        elif server_msg.type == "thinking":
            print(server_msg.payload.get("content", ""))
        elif server_msg.type == "done":
            print(f"\nDone: {server_msg.payload}")
        elif server_msg.type == "error":
            print(f"\nError: {server_msg.payload.get('message')}")
    
    print(f"\n\n=== Full Response ===")
    print(f"Length: {len(full_response)}")
    print(f"Contains read_file: {'read_file' in full_response}")
    
    # 手动解析
    tool_call = engine._parse_tool_call(full_response)
    print(f"\nParsed tool call: {tool_call}")

if __name__ == "__main__":
    asyncio.run(test_tool_call())