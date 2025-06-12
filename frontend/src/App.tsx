import React, { useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { useCodegen } from './hooks/useCodegen';
import { useThreads } from './hooks/useThreads';

function App() {
  const { config, isConnecting, updateConfig, runTask } = useCodegen();
  const { 
    threads, 
    activeThread, 
    activeThreadId, 
    setActiveThreadId, 
    createThread, 
    addMessage, 
    updateMessage,
    deleteThread 
  } = useThreads();

  // Handle task updates
  useEffect(() => {
    const handleTaskUpdate = async (event: CustomEvent) => {
      const { taskId, task } = event.detail;
      
      if (task && activeThread) {
        const message = activeThread.messages.find(m => m.taskId === taskId);
        if (message) {
          updateMessage(activeThread.id, message.id, {
            status: task.status,
            content: task.status === 'completed' && task.result 
              ? task.result
              : task.status === 'failed' && task.error
                ? `Error: ${task.error}`
                : task.status === 'running'
                  ? 'Processing your request...'
                  : message.content
          });
        }
      }
    };

    window.addEventListener('taskUpdate', handleTaskUpdate as EventListener);
    return () => window.removeEventListener('taskUpdate', handleTaskUpdate as EventListener);
  }, [activeThread, updateMessage]);

  const handleNewThread = () => {
    createThread();
  };

  const handleSendMessage = async (content: string) => {
    if (!activeThread || !config.isConnected) return;

    // Add user message
    addMessage(activeThread.id, {
      content,
      type: 'user'
    });

    try {
      // Run the task
      const task = await runTask(content);
      
      // Add assistant message with pending status
      addMessage(activeThread.id, {
        content: 'Processing your request...',
        type: 'assistant',
        taskId: task.id,
        status: task.status
      });

    } catch (error) {
      // Add error message
      addMessage(activeThread.id, {
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        type: 'error'
      });
    }
  };

  // Create initial thread if none exist
  useEffect(() => {
    if (threads.length === 0) {
      const thread = createThread('General');
      setActiveThreadId(thread.id);
    }
  }, []);

  return (
    <div className="h-screen flex bg-slate-100">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        config={config}
        isConnecting={isConnecting}
        onThreadSelect={setActiveThreadId}
        onNewThread={handleNewThread}
        onDeleteThread={deleteThread}
        onConfigUpdate={updateConfig}
      />
      
      <div className="flex-1">
        <ChatArea
          thread={activeThread}
          isConnected={config.isConnected}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  );
}
