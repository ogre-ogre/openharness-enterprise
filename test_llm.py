"""
测试 LLM 调用
"""
import sys
sys.path.insert(0, r'src')

from dotenv import load_dotenv
load_dotenv('.env')

from openharness.enterprise.llm.client import get_llm_client
import asyncio

async def test_llm():
    client = get_llm_client()
    
    messages = [
        {"role": "user", "content": "你好，请简单介绍一下你自己"}
    ]
    
    system_prompt = "你是一个有帮助的AI助手。"
    
    print("=== Testing LLM Call ===")
    print("Messages:", messages)
    print("System:", system_prompt)
    print("\n=== Response ===")
    
    try:
        full_response = ""
        async for chunk in client.stream_chat(messages, system_prompt):
            print(chunk, end="", flush=True)
            full_response += chunk
        print("\n\n=== Test Complete ===")
        print(f"Total length: {len(full_response)}")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())