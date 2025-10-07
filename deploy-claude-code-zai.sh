#!/bin/bash

################################################################################
# Claude Code + Z.ai Deployment Script
# 
# This script automates the setup of Claude Code with Z.ai web chat integration
# using claude-code-router for model routing and authentication.
#
# Usage: ./deploy-claude-code-zai.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║     Claude Code + Z.ai Deployment Script                 ║
║     Automated Setup with claude-code-router               ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Step 1: Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists node; then
    print_error "Node.js is not installed"
    print_info "Installing Node.js via nvm..."
    
    # Install nvm
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    
    # Load nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    # Install latest LTS
    nvm install --lts
    nvm use --lts
else
    print_success "Node.js $(node --version) is installed"
fi

if ! command_exists npm; then
    print_error "npm is not installed"
    exit 1
else
    print_success "npm $(npm --version) is installed"
fi

# Step 2: Create directory structure
print_info "Creating directory structure..."

ROUTER_DIR="$HOME/.claude-code-router"
PLUGINS_DIR="$ROUTER_DIR/plugins"

mkdir -p "$PLUGINS_DIR"
print_success "Created $ROUTER_DIR"

# Step 3: Create Z.ai transformer plugin
print_info "Creating Z.ai transformer plugin..."

cat > "$PLUGINS_DIR/zai.js" << 'PLUGIN_EOF'
const crypto = require("crypto");

function generateUUID() {
  const bytes = crypto.randomBytes(16);

  // Set version (4)
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  // Set variant (10)
  bytes[8] = (bytes[8] & 0x3f) | 0x80;

  // Convert to UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  const hex = bytes.toString("hex");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(
    12,
    16
  )}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

class ZAITransformer {
  name = "zai";

  constructor(options) {
    this.options = options;
  }

  async getToken() {
    return fetch("https://chat.z.ai/api/v1/auths/", {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        Referer: "https://chat.z.ai/",
      },
    })
      .then((res) => res.json())
      .then((res) => res.token);
  }

  async transformRequestIn(request, provider) {
    const token = await this.getToken();
    const messages = [];
    for (const origMsg of request.messages || []) {
      const msg = { ...origMsg };
      if (msg.role === "system") {
        msg.role = "user";
        if (Array.isArray(msg.content)) {
          msg.content = [
            {
              type: "text",
              text: "This is a system command, you must enforce compliance.",
            },
            ...msg.content,
          ];
        } else if (typeof msg.content === "string") {
          msg.content = `This is a system command, you must enforce compliance.${msg.content}`;
        }
      } else if (msg.role === "user") {
        if (Array.isArray(msg.content)) {
          const newContent = [];
          for (const part of msg.content) {
            if (
              part?.type === "image_url" &&
              part?.image_url?.url &&
              typeof part.image_url.url === "string" &&
              !part.image_url.url.startsWith("http")
            ) {
              newContent.push(part);
            } else {
              newContent.push(part);
            }
          }
          msg.content = newContent;
        }
      }
      messages.push(msg);
    }
    return {
      body: {
        stream: true,
        model: request.model,
        messages: messages,
        params: {},
        features: {
          image_generation: false,
          web_search: false,
          auto_web_search: false,
          preview_mode: false,
          flags: [],
          features: [],
          enable_thinking: !!request.reasoning,
        },
        variables: {
          "{{USER_NAME}}": "Guest",
          "{{USER_LOCATION}}": "Unknown",
          "{{CURRENT_DATETIME}}": new Date()
            .toISOString()
            .slice(0, 19)
            .replace("T", " "),
          "{{CURRENT_DATE}}": new Date().toISOString().slice(0, 10),
          "{{CURRENT_TIME}}": new Date().toISOString().slice(11, 19),
          "{{CURRENT_WEEKDAY}}": new Date().toLocaleDateString("en-US", {
            weekday: "long",
          }),
          "{{CURRENT_TIMEZONE}}":
            Intl.DateTimeFormat().resolvedOptions().timeZone,
          "{{USER_LANGUAGE}}": "zh-CN",
        },
        model_item: {},
        tools:
          !request.reasoning && request.tools?.length
            ? request.tools
            : undefined,
        chat_id: generateUUID(),
        id: generateUUID(),
      },
      config: {
        url: new URL("https://chat.z.ai/api/chat/completions"),
        headers: {
          Accept: "*/*",
          "Accept-Language": "zh-CN",
          Authorization: `Bearer ${token || ""}`,
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
          "Content-Type": "application/json",
          Origin: "https://chat.z.ai",
          Pragma: "no-cache",
          Referer: "https://chat.z.ai/",
          "Sec-Fetch-Dest": "empty",
          "Sec-Fetch-Mode": "cors",
          "Sec-Fetch-Site": "same-origin",
          "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
          "X-FE-Version": "prod-fe-1.0.77",
        },
      },
    };
  }

  async transformResponseOut(response, context) {
    if (response.headers.get("Content-Type")?.includes("application/json")) {
      let jsonResponse = await response.json();
      const res = {
        id: jsonResponse.id,
        choices: [
          {
            finish_reason: jsonResponse.choices[0].finish_reason || null,
            index: 0,
            message: {
              content: jsonResponse.choices[0].message?.content || "",
              role: "assistant",
              tool_calls:
                jsonResponse.choices[0].message?.tool_calls || undefined,
            },
          },
        ],
        created: parseInt(new Date().getTime() / 1000 + "", 10),
        model: jsonResponse.model,
        object: "chat.completion",
        usage: jsonResponse.usage || {
          completion_tokens: 0,
          prompt_tokens: 0,
          total_tokens: 0,
        },
      };
      return new Response(JSON.stringify(res), {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
      });
    } else if (response.headers.get("Content-Type")?.includes("stream")) {
      if (!response.body) {
        return response;
      }
      const isStream = !!context.req.body.stream;
      const result = {
        id: "",
        choices: [
          {
            finish_reason: null,
            index: 0,
            message: {
              content: "",
              role: "assistant",
            },
          },
        ],
        created: parseInt(new Date().getTime() / 1000 + "", 10),
        model: "",
        object: "chat.completion",
        usage: {
          completion_tokens: 0,
          prompt_tokens: 0,
          total_tokens: 0,
        },
      };

      const decoder = new TextDecoder();
      const encoder = new TextEncoder();

      let currentId = "";
      let currentModel = context?.req?.body?.model || "";

      let hasToolCall = false;
      let toolArgs = "";
      let toolId = "";
      let toolCallUsage = null;
      let contentIndex = 0;
      let hasThinking = false;

      const processLine = (line, controller, reader) => {
        if (line.startsWith("data:")) {
          const chunkStr = line.slice(5).trim();
          if (chunkStr) {
            try {
              let chunk = JSON.parse(chunkStr);

              if (chunk.type === "chat:completion") {
                const data = chunk.data;

                if (data.id) currentId = data.id;
                if (data.model) currentModel = data.model;

                if (data.phase === "tool_call") {
                  if (!hasToolCall) hasToolCall = true;
                  const blocks = data.edit_content.split("<glm_block >");
                  blocks.forEach((block, index) => {
                    if (!block.includes("</glm_block>")) return;
                    if (index === 0) {
                      toolArgs += data.edit_content.slice(
                        0,
                        data.edit_content.indexOf('"result') - 3
                      );
                    } else {
                      if (toolId) {
                        try {
                          toolArgs += '"';
                          const params = JSON.parse(toolArgs);
                          if (!isStream) {
                            result.choices[0].message.tool_calls.slice(
                              -1
                            )[0].function.arguments = params;
                          } else {
                            const deltaRes = {
                              choices: [
                                {
                                  delta: {
                                    role: "assistant",
                                    content: null,
                                    tool_calls: [
                                      {
                                        id: toolId,
                                        type: "function",
                                        function: {
                                          name: null,
                                          arguments: params,
                                        },
                                      },
                                    ],
                                  },
                                  finish_reason: null,
                                  index: contentIndex,
                                  logprobs: null,
                                },
                              ],
                              created: parseInt(
                                new Date().getTime() / 1000 + "",
                                10
                              ),
                              id: currentId || "",
                              model: currentModel || "",
                              object: "chat.completion.chunk",
                              system_fingerprint: "fp_zai_001",
                            };
                            controller.enqueue(
                              encoder.encode(
                                `data: ${JSON.stringify(deltaRes)}\n\n`
                              )
                            );
                          }
                        } catch (e) {
                          console.log("Parse error", toolArgs);
                        } finally {
                          toolArgs = "";
                          toolId = "";
                        }
                      }
                      contentIndex += 1;
                      const content = JSON.parse(block.slice(0, -12));
                      toolId = content.data.metadata.id;
                      toolArgs += JSON.stringify(
                        content.data.metadata.arguments
                      ).slice(0, -1);

                      if (!isStream) {
                        if (!result.choices[0].message.tool_calls) {
                          result.choices[0].message.tool_calls = [];
                        }
                        result.choices[0].message.tool_calls.push({
                          id: toolId,
                          type: "function",
                          function: {
                            name: content.data.metadata.name,
                            arguments: "",
                          },
                        });
                      } else {
                        const startRes = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                content: null,
                                tool_calls: [
                                  {
                                    id: toolId,
                                    type: "function",
                                    function: {
                                      name: content.data.metadata.name,
                                      arguments: "",
                                    },
                                  },
                                ],
                              },
                              finish_reason: null,
                              index: contentIndex,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(
                            `data: ${JSON.stringify(startRes)}\n\n`
                          )
                        );
                      }
                    }
                  });
                } else if (data.phase === "other") {
                  if (hasToolCall && data.usage) {
                    toolCallUsage = data.usage;
                  }
                  if (hasToolCall && data.edit_content?.startsWith("null,")) {
                    toolArgs += '"';
                    hasToolCall = false;
                    try {
                      const params = JSON.parse(toolArgs);
                      if (!isStream) {
                        result.choices[0].message.tool_calls.slice(
                          -1
                        )[0].function.arguments = params;
                        result.usage = toolCallUsage;
                        result.choices[0].finish_reason = "tool_calls";
                      } else {
                        const toolCallDelta = {
                          id: toolId,
                          type: "function",
                          function: {
                            name: null,
                            arguments: params,
                          },
                        };
                        const deltaRes = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                content: null,
                                tool_calls: [toolCallDelta],
                              },
                              finish_reason: null,
                              index: 0,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(
                            `data: ${JSON.stringify(deltaRes)}\n\n`
                          )
                        );

                        const finishRes = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                content: null,
                                tool_calls: [],
                              },
                              finish_reason: "tool_calls",
                              index: 0,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          usage: toolCallUsage || undefined,
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(
                            `data: ${JSON.stringify(finishRes)}\n\n`
                          )
                        );

                        controller.enqueue(encoder.encode(`data: [DONE]\n\n`));
                      }

                      reader.cancel();
                    } catch (e) {
                      console.log("Error", toolArgs);
                    }
                  }
                } else if (data.phase === "thinking") {
                  if (!hasThinking) hasThinking = true;
                  if (data.delta_content) {
                    const content = data.delta_content.startsWith("<details")
                      ? data.delta_content.split("</summary>\n>").pop().trim()
                      : data.delta_content;
                    if (!isStream) {
                      if (!result.choices[0].message?.thinking?.content) {
                        result.choices[0].message.thinking = {
                          content,
                        };
                      } else {
                        result.choices[0].message.thinking.content += content;
                      }
                    } else {
                      const msg = {
                        choices: [
                          {
                            delta: {
                              role: "assistant",
                              thinking: {
                                content,
                              },
                            },
                            finish_reason: null,
                            index: 0,
                            logprobs: null,
                          },
                        ],
                        created: parseInt(new Date().getTime() / 1000 + "", 10),
                        id: currentId || "",
                        model: currentModel || "",
                        object: "chat.completion.chunk",
                        system_fingerprint: "fp_zai_001",
                      };
                      controller.enqueue(
                        encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
                      );
                    }
                  }
                } else if (data.phase === "answer" && !hasToolCall) {
                  if (
                    data.edit_content &&
                    data.edit_content.includes("</details>\n")
                  ) {
                    if (hasThinking) {
                      const signature = Date.now().toString();
                      if (!isStream) {
                        result.choices[0].message.thinking.signature =
                          signature;
                      } else {
                        const msg = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                thinking: {
                                  content: "",
                                  signature,
                                },
                              },
                              finish_reason: null,
                              index: 0,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
                        );
                        contentIndex++;
                      }
                    }
                    const content = data.edit_content
                      .split("</details>\n")
                      .pop();
                    if (content) {
                      if (!isStream) {
                        result.choices[0].message.content += content;
                      } else {
                        const msg = {
                          choices: [
                            {
                              delta: {
                                role: "assistant",
                                content,
                              },
                              finish_reason: null,
                              index: 0,
                              logprobs: null,
                            },
                          ],
                          created: parseInt(
                            new Date().getTime() / 1000 + "",
                            10
                          ),
                          id: currentId || "",
                          model: currentModel || "",
                          object: "chat.completion.chunk",
                          system_fingerprint: "fp_zai_001",
                        };
                        controller.enqueue(
                          encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
                        );
                      }
                    }
                  }
                  if (data.delta_content) {
                    if (!isStream) {
                      result.choices[0].message.content += data.delta_content;
                    } else {
                      const msg = {
                        choices: [
                          {
                            delta: {
                              role: "assistant",
                              content: data.delta_content,
                            },
                            finish_reason: null,
                            index: 0,
                            logprobs: null,
                          },
                        ],
                        created: parseInt(new Date().getTime() / 1000 + "", 10),
                        id: currentId || "",
                        model: currentModel || "",
                        object: "chat.completion.chunk",
                        system_fingerprint: "fp_zai_001",
                      };
                      controller.enqueue(
                        encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
                      );
                    }
                  }
                  if (data.usage && !hasToolCall) {
                    if (!isStream) {
                      result.choices[0].finish_reason = "stop";
                      result.choices[0].usage = data.usage;
                    } else {
                      const msg = {
                        choices: [
                          {
                            delta: {
                              role: "assistant",
                              content: "",
                            },
                            finish_reason: "stop",
                            index: 0,
                            logprobs: null,
                          },
                        ],
                        usage: data.usage,
                        created: parseInt(new Date().getTime() / 1000 + "", 10),
                        id: currentId || "",
                        model: currentModel || "",
                        object: "chat.completion.chunk",
                        system_fingerprint: "fp_zai_001",
                      };
                      controller.enqueue(
                        encoder.encode(`data: ${JSON.stringify(msg)}\n\n`)
                      );
                    }
                  }
                }
              }
            } catch (error) {
              console.error(error);
            }
          }
        }
      };

      if (!isStream) {
        const reader = response.body.getReader();
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            processLine(line, null, reader);
          }
        }

        return new Response(JSON.stringify(result), {
          status: response.status,
          statusText: response.statusText,
          headers: {
            "Content-Type": "application/json",
          },
        });
      }

      const stream = new ReadableStream({
        start: async (controller) => {
          const reader = response.body.getReader();
          let buffer = "";
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) {
                controller.enqueue(encoder.encode(`data: [DONE]\n\n`));
                break;
              }

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");

              buffer = lines.pop() || "";

              for (const line of lines) {
                processLine(line, controller, reader);
              }
            }
          } catch (error) {
            controller.error(error);
          } finally {
            controller.close();
          }
        },
      });

      return new Response(stream, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    }
    return response;
  }
}

module.exports = ZAITransformer;
PLUGIN_EOF

print_success "Created zai.js plugin at $PLUGINS_DIR/zai.js"

# Step 4: Create configuration file
print_info "Creating configuration file..."

cat > "$ROUTER_DIR/config.js" << 'CONFIG_EOF'
{
  "LOG": false,
  "LOG_LEVEL": "debug",
  "CLAUDE_PATH": "",
  "HOST": "127.0.0.1",
  "PORT": 3456,
  "APIKEY": "",
  "API_TIMEOUT_MS": "600000",
  "PROXY_URL": "",
  "transformers": [
    {
      "name": "zai",
      "path": "~/.claude-code-router/plugins/zai.js",
      "options": {}
    }
  ],
  "Providers": [
    {
      "name": "GLM",
      "api_base_url": "http://127.0.0.1:8080/v1/chat/completions",
      "api_key": "sk-your-api-key",
      "models": ["GLM-4.5", "GLM-4.5-Air"],
      "transformers": {
        "use": ["zai"]
      }
    }
  ],
  "StatusLine": {
    "enabled": false,
    "currentStyle": "default",
    "default": {
      "modules": []
    },
    "powerline": {
      "modules": []
    }
  },
  "Router": {
    "default": "GLM,GLM-4.5",
    "background": "GLM,GLM-4.5",
    "think": "GLM,GLM-4.5",
    "longContext": "GLM,GLM-4.5",
    "longContextThreshold": 60000,
    "webSearch": "GLM,GLM-4.5",
    "image": "GLM,GLM-4.5"
  },
  "CUSTOM_ROUTER_PATH": ""
}
CONFIG_EOF

print_success "Created config.js at $ROUTER_DIR/config.js"

# Step 5: Install claude-code-router (if not already installed)
print_info "Checking for claude-code-router installation..."

if ! command_exists claude-code-router; then
    print_info "Installing claude-code-router globally..."
    npm install -g claude-code-router
    print_success "Installed claude-code-router"
else
    print_success "claude-code-router is already installed"
fi

# Step 6: Create helper scripts
print_info "Creating helper scripts..."

# Start script
cat > "$ROUTER_DIR/start.sh" << 'START_EOF'
#!/bin/bash
echo "Starting claude-code-router on port 3456..."
claude-code-router
START_EOF

chmod +x "$ROUTER_DIR/start.sh"
print_success "Created start.sh"

# Test script
cat > "$ROUTER_DIR/test.sh" << 'TEST_EOF'
#!/bin/bash

echo "Testing connection to Z.ai through claude-code-router..."
echo ""

curl -X POST http://127.0.0.1:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5",
    "messages": [
      {"role": "user", "content": "What model are you?"}
    ]
  }'

echo ""
echo "Test complete!"
TEST_EOF

chmod +x "$ROUTER_DIR/test.sh"
print_success "Created test.sh"

# Step 7: Print configuration instructions
echo ""
print_success "✨ Installation complete! ✨"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}📁 Configuration Location:${NC}"
echo "   $ROUTER_DIR"
echo ""
echo -e "${GREEN}📝 Configuration Files:${NC}"
echo "   • Plugin: $PLUGINS_DIR/zai.js"
echo "   • Config: $ROUTER_DIR/config.js"
echo ""
echo -e "${GREEN}🚀 Quick Start:${NC}"
echo "   1. Start the router:"
echo "      cd $ROUTER_DIR && ./start.sh"
echo ""
echo "   2. In another terminal, test the connection:"
echo "      cd $ROUTER_DIR && ./test.sh"
echo ""
echo "   3. Configure Claude Code to use:"
echo "      API Endpoint: http://127.0.0.1:3456/v1/chat/completions"
echo "      Model: GLM-4.5"
echo ""
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "   • Anonymous mode uses temporary tokens automatically"
echo "   • For full multimodal support, set your Z.ai token:"
echo "     - Visit https://chat.z.ai"
echo "     - Press F12 → Application → Cookies"
echo "     - Copy 'token' value"
echo "     - Set as environment variable: export ZAI_TOKEN='your-token'"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
print_info "For more information, see: https://github.com/your-repo/docs"
echo ""

