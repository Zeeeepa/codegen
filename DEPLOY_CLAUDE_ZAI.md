# 🚀 Claude Code + Z.ai Deployment Guide

Complete automated deployment script for integrating Claude Code with Z.ai's web chat interface using `claude-code-router`.

## 📋 Overview

This deployment automatically sets up:
- ✅ Z.ai transformer plugin for request/response translation
- ✅ Claude Code Router configuration
- ✅ Automatic token retrieval from Z.ai
- ✅ OpenAI-compatible API endpoint
- ✅ Multi-modal support (text, images, thinking mode)
- ✅ Tool calling capabilities

## 🔧 Prerequisites

The script will automatically install missing dependencies, but ideally you should have:
- Linux/macOS/WSL environment
- Bash shell
- Internet connection

The script will install:
- Node.js (via nvm)
- npm
- claude-code-router

## 🎯 Quick Start

### 1. Run the Deployment Script

```bash
# Download and run
curl -sSL https://raw.githubusercontent.com/your-repo/deploy-claude-code-zai.sh | bash

# Or if you have the script locally
chmod +x deploy-claude-code-zai.sh
./deploy-claude-code-zai.sh
```

### 2. Start the Router

```bash
cd ~/.claude-code-router
./start.sh
```

The router will start on `http://127.0.0.1:3456`

### 3. Test the Connection

In a new terminal:

```bash
cd ~/.claude-code-router
./test.sh
```

Expected output:
```json
{
  "id": "...",
  "model": "GLM-4.5",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "I am GLM-4.5, developed by Zhipu AI..."
    }
  }]
}
```

### 4. Configure Claude Code

Point your Claude Code instance to:
- **API Endpoint**: `http://127.0.0.1:3456/v1/chat/completions`
- **Model**: `GLM-4.5` or `GLM-4.5-Air`
- **API Key**: (leave empty or use dummy value)

## 📁 Installation Structure

After running the script, you'll have:

```
~/.claude-code-router/
├── config.js              # Router configuration
├── plugins/
│   └── zai.js            # Z.ai transformer plugin
├── start.sh              # Start the router
└── test.sh               # Test connection
```

## ⚙️ Configuration Details

### Anonymous Mode (Default)

The plugin automatically retrieves temporary tokens from Z.ai:
- ✅ No authentication required
- ✅ Works immediately
- ⚠️ Limited to basic features
- ⚠️ No conversation history

### Authenticated Mode (Recommended)

For full multimodal support and conversation history:

#### Option 1: Browser Token

1. Visit https://chat.z.ai and log in
2. Press `F12` to open Developer Tools
3. Go to: **Application** → **Cookies** → `https://chat.z.ai`
4. Find and copy the `token` value
5. Set as environment variable:
   ```bash
   export ZAI_TOKEN='your-token-here'
   ```

#### Option 2: API Key

1. Log in to Z.ai
2. Go to account settings
3. Generate an API key
4. Update `~/.claude-code-router/config.js`:
   ```javascript
   "api_key": "sk-your-actual-api-key"
   ```

### Config File Reference

Edit `~/.claude-code-router/config.js`:

```javascript
{
  "LOG": false,                    // Enable debug logging
  "HOST": "127.0.0.1",             // Router host
  "PORT": 3456,                    // Router port
  "API_TIMEOUT_MS": "600000",      // 10 minute timeout
  
  "Providers": [
    {
      "name": "GLM",
      "api_base_url": "http://127.0.0.1:8080/v1/chat/completions",
      "api_key": "sk-your-api-key",
      "models": ["GLM-4.5", "GLM-4.5-Air"],
      "transformers": {
        "use": ["zai"]             // Use Z.ai transformer
      }
    }
  ],
  
  "Router": {
    "default": "GLM,GLM-4.5",      // Default model
    "think": "GLM,GLM-4.5",        // Model for reasoning
    "image": "GLM,GLM-4.5",        // Model for vision
    "longContext": "GLM,GLM-4.5"   // Model for long contexts
  }
}
```

## 🎨 Features

### Supported Capabilities

✅ **Text Generation**
- Standard chat completions
- Streaming responses
- System message handling

✅ **Multi-Modal**
- Image understanding (with authenticated token)
- Vision + text reasoning

✅ **Reasoning Mode**
- Extended thinking with `enable_thinking: true`
- Thought process visibility

✅ **Tool Calling**
- OpenAI-compatible function calling
- Automatic tool execution

✅ **Context Variables**
- Dynamic user information
- Timezone awareness
- Date/time injection

## 🧪 Testing

### Basic Chat Test

```bash
curl -X POST http://127.0.0.1:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5",
    "messages": [
      {"role": "user", "content": "Hello! What model are you?"}
    ]
  }'
```

### Streaming Test

```bash
curl -X POST http://127.0.0.1:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5",
    "stream": true,
    "messages": [
      {"role": "user", "content": "Count to 5"}
    ]
  }'
```

### Reasoning Mode Test

```bash
curl -X POST http://127.0.0.1:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5",
    "reasoning": true,
    "messages": [
      {"role": "user", "content": "What is 23 * 47?"}
    ]
  }'
```

## 🔍 Troubleshooting

### Router Won't Start

```bash
# Check if port 3456 is already in use
lsof -i :3456

# Kill existing process
kill -9 $(lsof -t -i :3456)

# Try a different port in config.js
```

### Connection Refused

```bash
# Verify router is running
ps aux | grep claude-code-router

# Check logs
cd ~/.claude-code-router
tail -f router.log
```

### Token Expired

Anonymous tokens expire frequently. Solutions:
1. Restart the router (it will fetch a new token)
2. Use authenticated mode with your own token
3. Implement token refresh logic

### Plugin Not Loading

```bash
# Verify plugin file exists and is valid JavaScript
node -c ~/.claude-code-router/plugins/zai.js

# Check plugin path in config.js
# Ensure path uses absolute path or ~/ notation
```

## 🔐 Security Notes

### Anonymous Mode
- ⚠️ Tokens are temporary and public
- ⚠️ No conversation privacy
- ⚠️ Rate limits may apply
- ✅ Good for testing

### Authenticated Mode
- ✅ Your personal token/API key
- ✅ Conversation history saved
- ✅ Full feature access
- ⚠️ Keep tokens secure
- ⚠️ Don't commit tokens to version control

### Best Practices
1. Use environment variables for tokens
2. Never hardcode credentials in config files
3. Rotate tokens regularly
4. Use `.env` files with `.gitignore`
5. Consider using a secrets manager

## 📚 Advanced Usage

### Multiple Model Support

Edit `config.js` to add more models:

```javascript
"Providers": [
  {
    "name": "GLM",
    "models": ["GLM-4.5", "GLM-4.5-Air"],
    "transformers": { "use": ["zai"] }
  },
  {
    "name": "OpenAI",
    "api_base_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "sk-openai-key",
    "models": ["gpt-4", "gpt-3.5-turbo"]
  }
]
```

### Custom Router Logic

Create `~/.claude-code-router/custom-router.js`:

```javascript
module.exports = {
  route: (request) => {
    // Route based on message length
    const content = request.messages[0].content;
    if (content.length > 1000) {
      return { provider: "GLM", model: "GLM-4.5" };
    }
    return { provider: "GLM", model: "GLM-4.5-Air" };
  }
};
```

Update config.js:
```javascript
"CUSTOM_ROUTER_PATH": "~/.claude-code-router/custom-router.js"
```

### Environment-Specific Configs

```bash
# Development
export ROUTER_CONFIG=~/.claude-code-router/config.dev.js

# Production
export ROUTER_CONFIG=~/.claude-code-router/config.prod.js
```

## 🐛 Debug Mode

Enable detailed logging:

```javascript
// In config.js
{
  "LOG": true,
  "LOG_LEVEL": "debug"
}
```

View logs:
```bash
cd ~/.claude-code-router
tail -f debug.log
```

## 🔄 Updates

### Update the Plugin

```bash
cd ~/.claude-code-router/plugins
curl -O https://raw.githubusercontent.com/your-repo/zai.js
```

### Update claude-code-router

```bash
npm update -g claude-code-router
```

### Re-run Deployment

```bash
./deploy-claude-code-zai.sh
```

## 📖 Resources

- [Z.ai Official](https://chat.z.ai)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [GLM-4 Model Card](https://zhipuai.cn)

## 🤝 Contributing

Found a bug? Have an improvement?
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - feel free to use and modify!

## 🙏 Acknowledgments

- Z.ai team for the excellent AI models
- Claude Code for the incredible coding assistant
- OpenAI for the standard API format

---

**Happy Coding! 🎉**

If you encounter any issues, please open an issue on GitHub.

