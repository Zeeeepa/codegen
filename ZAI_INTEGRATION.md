# 🚀 Z.ai Integration in AutoGenLib

AutoGenLib now supports **Z.ai as the primary AI provider** with OpenAI as a fallback option. This integration provides enhanced AI capabilities using Z.ai's powerful language models.

## 📋 Features

### ✅ What's Integrated:

- **Z.ai Primary Support**: GLM-4 and other Z.ai models
- **OpenAI Fallback**: Seamless fallback if Z.ai is not available  
- **OpenAI-Compatible Interface**: Drop-in replacement for existing code
- **Comprehensive Error Resolution**: Enhanced diagnostic fixing with Z.ai
- **Automatic Model Selection**: Smart selection based on availability
- **Environment Configuration**: Easy setup with environment variables

## 🔧 Setup Instructions

### 1. Environment Variables

Set your Z.ai API key (preferred):
```bash
export ZAI_API_KEY="your-zai-api-key-here"
# OR
export ZHIPU_API_KEY="your-zhipu-api-key-here"

# Optional: Specify Z.ai model (defaults to glm-4)
export ZAI_MODEL="glm-4"
```

OpenAI fallback (optional):
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
export OPENAI_MODEL="gpt-4o"
```

### 2. Installation

The Z.ai SDK is automatically included in autogenlib:
```bash
# Already cloned in tools/autogenlib/z_ai_sdk/
# Dependencies in requirements.txt
pip install httpx typing-extensions
```

## 🎯 Usage

### Basic Usage

```python
import autogenlib

# Check AI availability
status = autogenlib.check_ai_availability()
print(f"Active AI: {status['active']}")  # "z.ai" or "openai"

# Get AI client (automatically selects best available)
client = autogenlib.get_ai_client()

# Use for error resolution (automatic Z.ai/OpenAI selection)
from autogenlib_ai_resolve import resolve_diagnostic_with_ai
result = resolve_diagnostic_with_ai(diagnostic, codebase)
```

### Direct Z.ai Usage

```python
from autogenlib._z_ai_client import get_z_ai_client, is_zai_available

if is_zai_available():
    client = get_z_ai_client()
    
    response = client.chat.create(
        model="glm-4",
        messages=[
            {"role": "user", "content": "Fix this Python code error"}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}  # OpenAI-compatible
    )
```

### Testing Connection

```python
from autogenlib._z_ai_client import test_zai_connection

status = test_zai_connection()
print(f"Z.ai Status: {status['status']}")
print(f"Message: {status['message']}")
```

## 📊 API Compatibility

The Z.ai integration provides **full OpenAI compatibility**:

| OpenAI Feature | Z.ai Support | Notes |
|----------------|--------------|-------|
| `chat.completions.create()` | ✅ | Full compatibility |
| JSON response format | ✅ | Automatically enforced |
| Temperature control | ✅ | 0.0 - 2.0 range |
| Max tokens | ✅ | Configurable limit |
| Streaming | ✅ | Real-time responses |
| Error handling | ✅ | OpenAI-compatible errors |

## 🔍 Available Models

### Z.ai Models:
- **`glm-4`** (default) - Latest GLM model
- **`charglm-3`** - Character role-playing 
- **`glm-4-vision`** - Multimodal capabilities
- **`glm-4-long`** - Long context support

### OpenAI Models (fallback):
- **`gpt-4o`** (default fallback)
- **`gpt-4`**
- **`gpt-3.5-turbo`**

## 🚀 Integration Points

### 1. AutoGenLib AI Resolution
```python
# autogenlib_ai_resolve.py automatically uses Z.ai
from autogenlib_ai_resolve import resolve_diagnostic_with_ai

# Uses Z.ai if available, falls back to OpenAI
result = resolve_diagnostic_with_ai(enhanced_diagnostic, codebase)
```

### 2. Graph-Sitter Backend
The FastAPI backend automatically detects and uses the best available AI service.

### 3. LSP Diagnostics
Enhanced diagnostics leverage Z.ai for better context understanding.

## ⚡ Performance & Benefits

### Z.ai Advantages:
- **🔥 Fast Response Times** - Optimized for code tasks
- **🧠 Better Code Understanding** - Trained on diverse code datasets  
- **🌐 Global Availability** - No regional restrictions
- **💰 Cost Effective** - Competitive pricing
- **🛡️ Privacy Focused** - Enhanced data protection

### Fallback Reliability:
- **🔄 Automatic Switching** - Seamless failover to OpenAI
- **📊 Smart Selection** - Uses best available model
- **⚖️ Load Balancing** - Distributes requests optimally

## 🔧 Configuration Options

### Environment Variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ZAI_API_KEY` | Z.ai API key | Required for Z.ai |
| `ZHIPU_API_KEY` | Alternative Z.ai key | Alternative |
| `ZAI_MODEL` | Z.ai model to use | `glm-4` |
| `OPENAI_API_KEY` | OpenAI fallback key | Optional |
| `OPENAI_MODEL` | OpenAI fallback model | `gpt-4o` |

### Runtime Configuration:
```python
# Force specific provider
from autogenlib._z_ai_client import ZAIWrapper
client = ZAIWrapper(api_key="custom-key")

# Check what's available
status = autogenlib.check_ai_availability()
print(status)
# {
#   "zai_available": True,
#   "openai_available": True, 
#   "active": "z.ai",
#   "recommended": "z.ai"
# }
```

## 🧪 Testing

Run the test suite:
```bash
# Test Z.ai integration
python -m pytest tests/graph_sitter_tools/test_z_ai_integration.py -v

# Test full functionality
python tests/graph_sitter_tools/test_all_tools.py
```

## 📋 Migration from OpenAI

Existing code using OpenAI will automatically benefit from Z.ai:

```python
# Before (OpenAI only)
import openai
client = openai.OpenAI()

# After (Z.ai + OpenAI fallback)
import autogenlib
client = autogenlib.get_ai_client()  # Automatically picks best option
```

No code changes required - the integration is transparent!

## 🆘 Troubleshooting

### Common Issues:

1. **Z.ai API key not found**:
   ```bash
   export ZAI_API_KEY="your-key-here"
   ```

2. **SDK import errors**:
   ```bash
   # Ensure dependencies are installed
   pip install httpx typing-extensions
   ```

3. **Model not found**:
   ```bash
   # Use supported models
   export ZAI_MODEL="glm-4"
   ```

4. **Connection issues**:
   ```python
   from autogenlib._z_ai_client import test_zai_connection
   print(test_zai_connection())
   ```

### Debug Mode:
```python
import logging
logging.getLogger('autogenlib').setLevel(logging.DEBUG)
```

## 🌟 Best Practices

1. **Set Z.ai as Primary**: Configure `ZAI_API_KEY` for best performance
2. **Keep OpenAI as Backup**: Set `OPENAI_API_KEY` for reliability  
3. **Use Appropriate Models**: `glm-4` for code, `charglm-3` for conversations
4. **Monitor Usage**: Track API usage across both providers
5. **Test Regularly**: Verify both Z.ai and OpenAI connections

## 🚀 Ready to Use!

Your AutoGenLib installation now intelligently uses Z.ai for superior AI-powered code analysis and error resolution, with seamless OpenAI fallback for maximum reliability.

**Enjoy the enhanced AI capabilities!** 🎉