# 大模型配置指南

本文档说明如何配置自定义 API 地址和 Key，支持多种大模型服务。
配合 [README.md](../README.md) 的快速开始食用，本文聚焦"如何把 LLM 跑起来"。
系统整体处理流程请看 [PIPELINE.md](PIPELINE.md)，各功能模块技术细节请看 [FEATURES.md](FEATURES.md)。

## 配置项说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `LLM_PROVIDER` | API类型 | `openai` / `anthropic` |
| `LLM_API_BASE_URL` | API地址 | `https://api.openai.com/v1` |
| `LLM_API_KEY` | API密钥 | `sk-xxxxx` |
| `LLM_MODEL_NAME` | 模型名称 | `gpt-4o` |
| `LLM_USE_ANTHROPIC_FORMAT` | 是否使用Anthropic格式 | `false` |

## 常见配置场景

### 1. OpenAI官方API

```env
LLM_PROVIDER=openai
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-xxxxxxxxxxxxx
LLM_MODEL_NAME=gpt-4o
LLM_USE_ANTHROPIC_FORMAT=false
```

### 2. Anthropic Claude API

```env
LLM_PROVIDER=anthropic
LLM_API_BASE_URL=https://api.anthropic.com
LLM_API_KEY=sk-ant-xxxxxxxxxxxxx
LLM_MODEL_NAME=claude-3-5-sonnet-20241022
LLM_USE_ANTHROPIC_FORMAT=true
```

### 3. Ollama本地部署

前提：已安装并启动Ollama

```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 拉取模型
ollama pull qwen2:7b
# 或
ollama pull llama3:8b
```

配置：
```env
LLM_PROVIDER=openai
LLM_API_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL_NAME=qwen2:7b
LLM_USE_ANTHROPIC_FORMAT=false
```

### 4. vLLM部署

前提：已安装并启动vLLM

```bash
# 启动vLLM服务
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000
```

配置：
```env
LLM_PROVIDER=openai
LLM_API_BASE_URL=http://localhost:8000/v1
LLM_API_KEY=not-needed
LLM_MODEL_NAME=Qwen/Qwen2-7B-Instruct
LLM_USE_ANTHROPIC_FORMAT=false
```

### 5. 第三方API代理

适用于国内大模型API代理、OpenAI中转服务等：

```env
LLM_PROVIDER=openai
LLM_API_BASE_URL=https://your-proxy.example.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL_NAME=gpt-4o
LLM_USE_ANTHROPIC_FORMAT=false
```

### 6. Azure OpenAI

```env
LLM_PROVIDER=openai
LLM_API_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment/
LLM_API_KEY=your-azure-api-key
LLM_MODEL_NAME=gpt-4
LLM_USE_ANTHROPIC_FORMAT=false
```

## 测试配置

启动后端服务后，访问以下接口测试LLM连接：

```bash
curl http://localhost:8000/api/tasks/test-llm
```

成功响应示例：
```json
{
  "status": "success",
  "llm_info": {
    "provider": "openai",
    "api_base_url": "http://localhost:11434/v1",
    "model_name": "qwen2:7b",
    "use_anthropic_format": false,
    "api_key_set": true
  },
  "response": "连接成功"
}
```

## 常见问题

### Q: 如何选择LLM_PROVIDER？

- 如果使用OpenAI或兼容OpenAI格式的服务（如Ollama、vLLM），选择 `openai`
- 如果直接使用Anthropic Claude API，选择 `anthropic`

### Q: LLM_USE_ANTHROPIC_FORMAT什么时候设置为true？

只有当 `LLM_PROVIDER=anthropic` 且直接使用Anthropic官方API时才设置为true。

### Q: 推荐使用哪个模型？

- **性能优先**：GPT-4o、Claude-3.5-Sonnet
- **性价比**：Qwen2-7B、DeepSeek-Coder-7B（本地部署）
- **免费/低成本**：Ollama本地部署

### Q: 如何提高Agent的搜索效果？

1. 使用能力较强的模型（如GPT-4o、Claude-3.5）
2. 确保SerpAPI Key配置正确
3. 在职位配置中添加详细的关键词
