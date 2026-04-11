import asyncio
from openharness.enterprise.users.context import load_user_context
from openharness.enterprise.storage.database import get_database
from openharness.enterprise.llm.client import get_llm_client

async def test_llm_skill_injection():
    # 加载用户上下文
    db = get_database()
    user = db.get_user_by_username("admin")
    ctx = load_user_context(user)
    
    print("=== User Context ===")
    print("Available skills:", ctx.available_skills)
    print("Skills path:", ctx.skills_path)
    
    # 测试 LLM client 构建 system prompt
    llm = get_llm_client()
    
    # 模拟 webchat.py 中的调用
    system_prompt = "你是一个有帮助的 AI 助手。"
    
    # 测试 build_system_prompt
    full_prompt = llm.build_system_prompt(
        base_prompt=system_prompt,
        skills=ctx.available_skills,
        skills_base_path=ctx.skills_path
    )
    
    print("\n=== Full System Prompt ===")
    print("Length:", len(full_prompt))
    
    # 检查是否包含 queryZhandianByCity skill
    if "queryZhandianByCity" in full_prompt:
        print("\n[OK] queryZhandianByCity skill found in prompt!")
    else:
        print("\n[FAIL] queryZhandianByCity skill NOT found!")
    
    if "queryStation" in full_prompt:
        print("[OK] Skill content injected (name: queryStation)")
    
    if "站点" in full_prompt:
        print("[OK] Skill description injected")
    
    # 打印 skill 相关部分
    if "Skill: queryZhandianByCity" in full_prompt:
        start = full_prompt.find("Skill: queryZhandianByCity")
        print("\n--- Skill Content Preview ---")
        print(full_prompt[start:start+500])

asyncio.run(test_llm_skill_injection())