# OpenHarness Enterprise 更新日志

## [2026-04-10] SQLite 兼容性修复

### 修复
- **SQLite TRUE/FALSE 兼容性问题**
  - SQLite 不支持 `TRUE`/`FALSE` 关键字，改用 `1`/`0`
  - 修复 `database.py` 中所有 SQL 查询：
    - `get_user_by_api_key`: `is_active = TRUE` → `is_active = 1`
    - `update_api_key`: `api_key_enabled = TRUE` → `api_key_enabled = 1`
    - `get_user_sessions`: `is_active = TRUE` → `is_active = 1`
    - `get_active_session_count`: `is_active = TRUE` → `is_active = 1`
  - 修复表定义中的 `DEFAULT TRUE` → `DEFAULT 1`

### 影响
- 修复了远程部署环境历史对话窗口不显示的问题
- 历史会话 API 现在可以正常返回数据

### 部署步骤
1. 更新 `src/openharness/enterprise/storage/database.py`
2. 更新数据库中已存储的字符串 "TRUE" 为数字 1:
   ```sql
   UPDATE sessions SET is_active = 1 WHERE is_active = 'TRUE';
   UPDATE users SET is_active = 1, api_key_enabled = 1 WHERE is_active = 'TRUE' OR api_key_enabled = 'TRUE';
   ```
3. 重启服务