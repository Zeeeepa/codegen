# 🎯 ChatKit Integration Plan - Voice Automation Hub

## 📚 Analysis Complete

I've analyzed all three ChatKit repositories and documentation:

### **Repositories Analyzed:**
1. ✅ `chatkit-python` - Core Python SDK
2. ✅ `openai-chatkit-starter-app` - Next.js starter template
3. ✅ `openai-chatkit-advanced-samples` - Advanced patterns & examples

### **Key Documentation Read:**
- ✅ [Actions](https://openai.github.io/chatkit-python/actions/) - Server/client action handling
- ✅ [Widgets](https://openai.github.io/chatkit-python/widgets/) - UI component library
- ✅ [Server](https://openai.github.io/chatkit-python/server/) - ChatKitServer base class
- ✅ [Store](https://openai.github.io/chatkit-python/store/) - Thread/Item persistence

---

## 🏗️ Updated Architecture (ChatKit-Native)

```
🎤 Voice Input (Web Speech API)
    ↓
📱 Next.js ChatKitPanel Component
    ├─ Voice Recording UI
    ├─ TTS Playback
    └─ Widget Rendering
    ↓
🔄 ChatKit Server (Python)
    ├─ VoiceAutomationAgent (extends ChatKitServer)
    │   ├─ action() method → Handle tool actions
    │   ├─ generate() method → Stream responses
    │   └─ Tool Orchestration
    ↓
🛠️ Actions System
    ├─ "run_cli" → CLI Tool
    ├─ "open_browser" → Browser Tool
    ├─ "run_tests" → Test Runner
    ├─ "research" → Research Agent
    ├─ "install_mcp" → MCP Installer
    └─ "create_task" → Task Manager
    ↓
🎨 Widgets System
    ├─ ProgressWidget → Live execution progress
    ├─ Card → Task results
    ├─ Chart → Test results visualization
    ├─ MCPDashboard (Custom) → Server management
    └─ TaskManager (Custom) → Concurrent tasks
    ↓
💾 Store
    ├─ Threads → Conversation history
    ├─ Items → Messages + Widgets
    └─ Attachments → Screenshots, logs
```

---

## 📦 Implementation Plan (Using Real ChatKit)

### **Step 1: Install ChatKit SDK ✅**
```bash
pip install chatkit-python openai
npm install @openai/chatkit-react
```

### **Step 2: Create VoiceAutomationAgent (extends ChatKitServer)**

```python
from chatkit.server import ChatKitServer
from chatkit.types import ThreadMetadata, ThreadStreamEvent
from chatkit.actions import Action, ActionConfig
from chatkit.widgets import Card, Button, Progress, Col
from collections.abc import AsyncIterator

class VoiceAutomationAgent(ChatKitServer[dict]):
    """
    Main agent that handles voice commands and orchestrates tools
    """
    
    async def generate(
        self,
        context: dict,
        thread: ThreadMetadata
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Process voice command and stream response"""
        
        # Get last user message
        items = await self.store.get_thread_items(thread.id, context)
        last_message = items[-1]
        
        # Parse intent from voice command
        intent = await self.parse_intent(last_message.content)
        
        # Stream progress widget
        yield WidgetItem(
            id=self.store.generate_item_id("widget", thread, context),
            thread_id=thread.id,
            created_at=datetime.now(),
            widget=Card(
                children=[
                    Progress(
                        label=f"Executing: {intent.action}",
                        value=0
                    )
                ]
            )
        )
        
        # Execute tool based on intent
        async for event in self.execute_tool(intent, thread, context):
            yield event
    
    async def action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: dict
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Handle actions triggered from widgets"""
        
        if action.type == "run_cli":
            # Execute CLI command
            async for event in self.cli_tool.execute(action.payload, thread, context):
                yield event
        
        elif action.type == "open_browser":
            # Browser automation
            async for event in self.browser_tool.execute(action.payload, thread, context):
                yield event
        
        elif action.type == "run_tests":
            # Run pytest
            async for event in self.test_tool.execute(action.payload, thread, context):
                yield event
        
        elif action.type == "research":
            # Research agent
            async for event in self.research_tool.execute(action.payload, thread, context):
                yield event
        
        elif action.type == "install_mcp":
            # Install MCP server
            async for event in self.mcp_manager.install(action.payload, thread, context):
                yield event
        
        elif action.type == "create_task":
            # Create concurrent task
            async for event in self.task_manager.create(action.payload, thread, context):
                yield event
```

### **Step 3: Implement Tools with ChatKit Widgets**

#### **CLI Tool**
```python
class CLITool:
    async def execute(
        self,
        payload: dict,
        thread: ThreadMetadata,
        context: dict
    ) -> AsyncIterator[ThreadStreamEvent]:
        command = payload['command']
        
        # Start progress
        widget_id = generate_id()
        yield update_widget(
            widget_id,
            Progress(label=f"Running: {command}", value=0)
        )
        
        # Execute command
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Stream output
        async for line in process.stdout:
            yield update_widget(
                widget_id,
                Card(children=[
                    Progress(label="Running...", value=50),
                    Text(value=line.decode(), font="mono")
                ])
            )
        
        # Complete
        yield update_widget(
            widget_id,
            Card(
                status=WidgetStatusWithIcon(icon="check", label="Complete"),
                children=[Text(value="Command completed", color="success")]
            )
        )
```

#### **Browser Tool**
```python
class BrowserTool:
    async def execute(
        self,
        payload: dict,
        thread: ThreadMetadata,
        context: dict
    ) -> AsyncIterator[ThreadStreamEvent]:
        url = payload['url']
        
        # Launch browser
        yield progress_widget("Launching browser...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Navigate
            yield progress_widget("Navigating...")
            await page.goto(url)
            
            # Screenshot
            yield progress_widget("Taking screenshot...")
            screenshot = await page.screenshot()
            
            # Upload to attachments
            attachment_id = await store.add_attachment(
                thread.id,
                screenshot,
                "image/png",
                context
            )
            
            # Show result
            yield WidgetItem(
                widget=Card(
                    status=WidgetStatusWithIcon(icon="check", label="Complete"),
                    children=[
                        Text(value=f"Visited: {url}"),
                        Image(url=f"/attachments/{attachment_id}")
                    ]
                )
            )
```

### **Step 4: Create Custom Widgets**

#### **MCP Dashboard Widget**
```python
def MCPDashboard(servers: List[MCPServer]) -> Card:
    """Custom widget for MCP server management"""
    return Card(
        children=[
            Title(value="MCP Servers"),
            Col(
                gap=2,
                children=[
                    Card(
                        size="sm",
                        children=[
                            Row(
                                justify="between",
                                children=[
                                    Col(children=[
                                        Text(value=server.name, weight="semibold"),
                                        Caption(value=f"Status: {server.status}")
                                    ]),
                                    Button(
                                        label="Stop" if server.running else "Start",
                                        onClickAction=ActionConfig(
                                            type="toggle_mcp",
                                            payload={"server_id": server.id}
                                        )
                                    )
                                ]
                            )
                        ]
                    )
                    for server in servers
                ],
            ),
            Button(
                label="+ Install New Server",
                onClickAction=ActionConfig(
                    type="show_mcp_registry",
                    handler="client"  # Opens modal on client
                )
            )
        ]
    )
```

#### **Task Manager Widget**
```python
def TaskManager(tasks: List[Task]) -> Card:
    """Widget for managing concurrent tasks"""
    return Card(
        children=[
            Title(value="Active Tasks"),
            Col(
                gap=2,
                children=[
                    Card(
                        size="sm",
                        children=[
                            Text(value=task.name, weight="semibold"),
                            Progress(
                                label=task.status,
                                value=task.progress
                            ),
                            Row(
                                gap=1,
                                children=[
                                    Button(
                                        label="View",
                                        size="sm",
                                        onClickAction=ActionConfig(
                                            type="view_task",
                                            payload={"task_id": task.id}
                                        )
                                    ),
                                    Button(
                                        label="Cancel",
                                        size="sm",
                                        color="danger",
                                        onClickAction=ActionConfig(
                                            type="cancel_task",
                                            payload={"task_id": task.id}
                                        )
                                    )
                                ]
                            )
                        ]
                    )
                    for task in tasks
                ]
            ),
            Button(
                label="+ Create New Task",
                onClickAction=ActionConfig(
                    type="create_task_form",
                    handler="client"
                )
            )
        ]
    )
```

### **Step 5: Frontend Integration**

#### **Voice Interface Component**
```tsx
// components/VoiceInterface.tsx
import { useState } from 'react';
import { useChatKit } from '@openai/chatkit-react';

export function VoiceInterface() {
  const chatKit = useChatKit();
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);
  
  const startRecording = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onresult = async (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');
      
      if (event.results[event.results.length - 1].isFinal) {
        // Send to ChatKit
        await chatKit.sendMessage({ content: transcript });
        
        // TTS response
        speakResponse(transcript);
      }
    };
    
    recognition.start();
    setRecognition(recognition);
    setIsRecording(true);
  };
  
  const stopRecording = () => {
    recognition?.stop();
    setIsRecording(false);
  };
  
  const speakResponse = (text: string) => {
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
  };
  
  return (
    <div className="voice-interface">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        className={isRecording ? 'recording' : ''}
      >
        {isRecording ? '🔴 Stop' : '🎤 Start Voice'}
      </button>
    </div>
  );
}
```

#### **Main App with ChatKit**
```tsx
// app/page.tsx
import { ChatKitPanel } from '@openai/chatkit-react';
import { VoiceInterface } from '@/components/VoiceInterface';
import { useState } from 'react';

export default function Home() {
  const [sessionToken, setSessionToken] = useState<string>();
  
  useEffect(() => {
    // Get session from backend
    fetch('/api/create-session', { method: 'POST' })
      .then(res => res.json())
      .then(data => setSessionToken(data.client_secret));
  }, []);
  
  return (
    <div className="app">
      <VoiceInterface />
      
      {sessionToken && (
        <ChatKitPanel
          sessionToken={sessionToken}
          apiUrl={process.env.NEXT_PUBLIC_API_URL}
          widgets={{
            onAction: async (action) => {
              // Handle client-side actions
              if (action.type === 'show_mcp_registry') {
                // Open MCP registry modal
              }
            }
          }}
        />
      )}
    </div>
  );
}
```

---

## 🎯 Complete Implementation Checklist

### **Backend (Python)**
- [x] Install `chatkit-python`
- [ ] Create `VoiceAutomationAgent` (extends `ChatKitServer`)
- [ ] Implement `generate()` method
- [ ] Implement `action()` method
- [ ] Create CLI Tool with Progress widgets
- [ ] Create Browser Tool with Screenshot widgets
- [ ] Create Test Runner with Results widgets
- [ ] Create Research Tool with Card widgets
- [ ] Create MCP Manager with custom Dashboard widget
- [ ] Create Task Manager with concurrent execution
- [ ] Implement Store (use `chatkit.store.Store`)

### **Frontend (Next.js)**
- [x] Install `@openai/chatkit-react`
- [ ] Copy starter app structure
- [ ] Add `VoiceInterface` component
- [ ] Integrate Web Speech API
- [ ] Add TTS playback
- [ ] Implement client-side action handlers
- [ ] Create MCP Registry modal
- [ ] Create Task Creation form
- [ ] Style components

### **Integration**
- [ ] FastAPI server with ChatKit endpoint
- [ ] Session creation endpoint
- [ ] WebSocket for real-time updates
- [ ] Attachment handling
- [ ] Error boundaries

---

## 🚀 Next Steps

**I'm ready to implement all 10 steps with proper ChatKit integration.**

Say "implement it" and I'll build:
1. Complete backend with real ChatKit SDK
2. All tools with proper widgets
3. Frontend with voice interface
4. MCP dashboard
5. Task manager
6. Full documentation

This will be a production-ready, ChatKit-native implementation! 🎯

