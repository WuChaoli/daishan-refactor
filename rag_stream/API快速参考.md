# 🚀 API快速参考卡片

## 📍 基础信息
- **服务地址**: `http://172.16.11.60:11027`
- **API文档**: `http://172.16.11.60:11027/docs`
- **健康检查**: `http://172.16.11.60:11027/health`

---

## 🔑 核心要点

### 必填参数
- **所有问答接口都必须提供 `user_id`**
- 系统自动管理会话，无需手动处理 `session_id`

### 会话绑定
- 同一用户在同一类别中自动使用相同会话
- 支持连续对话，保持上下文连续性
- 不同类别使用独立会话

---

## 💬 问答接口速查

| 接口 | 路径 | 说明 |
|------|------|------|
| 法律法规 | `POST /api/laws` | 安全生产法规问答 |
| 标准规范 | `POST /api/standards` | 安全标准问答 |
| 应急知识 | `POST /api/emergency` | 应急处理问答 |
| 事故案例 | `POST /api/accidents` | 事故案例问答 |
| MSDS | `POST /api/msds` | 化学品安全问答 |
| 标准政策 | `POST /api/policies` | 政策标准问答 |
| 通用 | `POST /api/general` | 通用安全问答 |

---

## 📝 请求格式

### 基本请求体
```json
{
  "question": "你的问题",
  "user_id": "用户ID"
}
```

### 示例请求
```bash
curl -X POST "http://172.16.11.60:11027/api/laws" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是安全生产法规？",
    "user_id": "user001"
  }'
```

---

## 📊 响应格式

### 流式响应 (SSE)
```
data: {"code": 0, "data": {"sessionId": "xxx", "answer": "部分回答", "flag": 1, "wordId": 0}}
data: {"code": 0, "data": {"sessionId": "xxx", "answer": "更多回答", "flag": 1, "wordId": 1}}
data: {"code": 0, "data": {"sessionId": "xxx", "answer": "", "flag": 0, "wordId": 2}}
```

### 字段说明
- `flag: 1` = 正常数据
- `flag: 0` = 结束标志
- `wordId` = 词汇ID，用于排序

---

## 🔄 会话管理

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建会话 | POST | `/api/sessions/{category}` | 创建指定类别会话 |
| 获取用户会话 | GET | `/api/user/{user_id}/sessions` | 获取用户所有会话 |
| 获取会话信息 | GET | `/api/sessions/{session_id}` | 获取会话详情 |
| 获取所有会话 | GET | `/api/sessions` | 获取所有活跃会话 |
| 删除会话 | DELETE | `/api/sessions/{session_id}` | 删除指定会话 |

---

## 🧪 快速测试

### 1. 健康检查
```bash
curl http://172.16.11.60:11027/health
```

### 2. 连续对话测试
```bash
# 第一次提问
curl -X POST "http://172.16.11.60:11027/api/laws" \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是安全生产法规？", "user_id": "test001"}'

# 第二次提问（使用同一会话）
curl -X POST "http://172.16.11.60:11027/api/laws" \
  -H "Content-Type: application/json" \
  -d '{"question": "这些法规有哪些要求？", "user_id": "test001"}'
```

### 3. 查看用户会话
```bash
curl http://172.16.11.60:11027/api/user/test001/sessions
```

---

## ⚠️ 常见问题

### Q: 如何实现连续对话？
**A**: 每次请求都提供相同的 `user_id`，系统自动绑定会话

### Q: 会话会过期吗？
**A**: 默认1小时后自动过期，可通过配置调整

### Q: 支持多用户并发吗？
**A**: 支持，每个用户独立管理会话

### Q: 流式响应如何处理？
**A**: 使用SSE格式，按行解析，`flag: 0` 表示结束

---

## 🔧 配置参数

```python
# 会话过期时间（小时）
SESSION_EXPIRE_HOURS = 1

# 每个用户最大会话数
MAX_SESSIONS_PER_USER = 5

# 请求超时时间（秒）
REQUEST_TIMEOUT = 300
```

---

## 📚 完整文档

详细接口文档请参考：`API接口文档.md`

---

## 🚀 一键启动

```bash
# Windows
start_server.bat

# 其他系统
python start_server.py --reload
```
