import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useChatWebSocket } from './services/websocket.service';
import { ReadyState } from 'react-use-websocket';
import MessageComponent from './components/MessageComponent';
import AgentTOC from './components/AgentTOC';
import { simulateEvents } from './placeholderData';
import logoUrl from './assets/pic.png';
import logoSquareUrl from './assets/logo-square.png';
import type {
  Event,
  TextDeltaContent,
  ExampleContent,
  PlanItem,
  WorkerItem,
  ReportItem,
  OrchestraContent
} from './types/events';
import type {
  Message,
  ToolCallMessage,
} from './types/message';

const initialMessages: Message[] = [
  {
    id: 1,
    content: 'Hello! I am your AI assistant. How can I help you today?',
    sender: 'assistant',
    timestamp: new Date()
  }
];

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [exampleQuery, setExampleQuery] = useState<string[]>([]);
  const [hideExampleQuery, setHideExampleQuery] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [wsUrl, setWsUrl] = useState(localStorage.getItem('wsUrl') || 'ws://localhost:8848/ws');
  const { sendQuery, lastMessage, readyState } = useChatWebSocket(wsUrl);
  const [inputValue, setInputValue] = useState('');
  const [isModelResponding, setIsModelResponding] = useState(false);
  // const messagesEndRef = useRef<HTMLDivElement>(null);
  const mainContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const [hasUserSentMessage, setHasUserSentMessage] = useState(false);
  const [isUserAtBottom, setIsUserAtBottom] = useState(true);
  const handleEvent = (event: Event) => {
    console.log('current messages', messages);
    if (event.type === 'example') {
      const data = event.data as ExampleContent;
      const query = data.query;
      if (query) {
        setExampleQuery([query]);
      }
      return;
    }
    if (event.type === 'raw') {
      const data = event.data as TextDeltaContent;

      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];

        if (data.type == "tool_call") {
          // create new message
          const newMessage: Message = {
            id: Date.now(),
            content: {
              toolName: data.delta || "",
              toolCallArgument: data.argument || "",
              toolCallOutput: "",
              callid: data.callid || "",
            },
            sender: 'assistant',
            timestamp: new Date(),
            type: "tool_call",
            inprogress: true,
            requireConfirm: event.requireConfirm,
          };
          return [...prev, newMessage];
        }

        if (data.type == "tool_call_output") {
          // find tool_call with same callid
          const tool_call_message = prev.find((message) => message.type == "tool_call" && (message.content as ToolCallMessage).callid == data.callid);
          if (tool_call_message) {
            const updatedMessage: Message = {
              ...tool_call_message,
              content: {
                ...(tool_call_message.content as ToolCallMessage),
                toolCallOutput: data.delta,
              },
              inprogress: false,
              requireConfirm: event.requireConfirm,
            };
            // update tool_call_message
            const messageIndex = prev.findIndex(message =>
              message.type === "tool_call" &&
              (message.content as ToolCallMessage).callid === data.callid
            );
            if (messageIndex !== -1) {
              const updatedMessages = [...prev];
              updatedMessages[messageIndex] = updatedMessage;
              return updatedMessages;
            }
            return prev;
          }
        }

        // If last message is in progress and has the same type, update it
        if (lastMessage?.inprogress && (lastMessage.type == data.type)) {
          const updatedMessage: Message = {
            ...lastMessage,
            content: lastMessage.content + data.delta,
            inprogress: data.inprogress,
            requireConfirm: event.requireConfirm,
          };
          return [...prev.slice(0, -1), updatedMessage];
        }

        if (data.type == "text" || data.type == "reason") {
          // Otherwise, add a new non-tool message
          const newMessage: Message = {
            id: Date.now(),
            content: data.delta,
            sender: 'assistant',
            timestamp: new Date(),
            type: data.type,
            inprogress: data.inprogress,
            requireConfirm: event.requireConfirm,
          };
          return [...prev, newMessage];
        }

        return prev
      });
    } else if (event.type === 'new') {
      const data = event.data as { name: string };
      const message: Message = {
        id: Date.now() + 1,
        content: data.name,
        sender: 'assistant',
        timestamp: new Date(),
        type: 'new_agent',
        inprogress: true,
        requireConfirm: event.requireConfirm,
      };
      setMessages(prev => [...prev, message]);
      
      // Simulate agent initialization
      setTimeout(() => {
        setMessages(prev => {
          const updatedMessages = [...prev];
          const agentMessageIndex = updatedMessages.findIndex(m => m.id === message.id);
          if (agentMessageIndex !== -1) {
            updatedMessages[agentMessageIndex] = {
              ...updatedMessages[agentMessageIndex],
              inprogress: false,
            };
          }
          return updatedMessages;
        });
      }, 1500);
    } else if (event.type === 'orchestra') {
      const data = event.data as OrchestraContent;
      if (data.type === 'plan') {
        const item = data.item as PlanItem;
        // setPinnedPlan(item);
        const message: Message = {
          id: Date.now() + 1,
          content: item,
          sender: 'assistant',
          timestamp: new Date(),
          type: 'plan',
          requireConfirm: event.requireConfirm,
        }
        setMessages(prev => [...prev, message]);
      } else if (data.type === 'worker') {
        const item = data.item as WorkerItem;
        const message: Message = {
          id: Date.now() + 1,
          content: "task: \n" + item.task + '\n\n' + "output: \n" + item.output,
          sender: 'assistant',
          timestamp: new Date(),
          type: 'worker',
          requireConfirm: event.requireConfirm,
        };
        setMessages(prev => [...prev, message]);
      } else if (data.type === 'report') {
        const item = data.item as ReportItem;
        const message: Message = {
          id: Date.now() + 1,
          content: "report: \n" + item.output,
          sender: 'assistant',
          timestamp: new Date(),
          type: 'report',
          requireConfirm: event.requireConfirm,
        };
        setMessages(prev => [...prev, message]);
      }
    } else if (event.type === 'finish') {
      setIsModelResponding(false); // Call save function on finish
    } else {
      console.error('Unknown event type:', event.type);
    }
  }

  useEffect(() => {
    // Focus input on mount
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (lastMessage !== null) {
      const message_raw = lastMessage;
      const message_json = JSON.parse(message_raw.data);

      // parse to event
      const event: Event = message_json;
      console.log(event);
      handleEvent(event);
      if (isUserAtBottom) {
        scrollToBottom();
      }
    }
  }, [lastMessage]);

  const handleSendMessage = () => {
    if (!inputValue.trim() || isModelResponding) return;

    // Mark that user has sent their first message
    if (!hasUserSentMessage) {
      setHasUserSentMessage(true);
    }

    if (!hideExampleQuery) {
      setHideExampleQuery(true);
    }

    // Add user message to chat
    const userMessage: Message = {
      id: Date.now(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsModelResponding(true);

    if (readyState !== ReadyState.OPEN) {
      console.error("WebSocket is not connected");
      const message: Message = {
        id: Date.now() + 1,
        content: "WebSocket is not connected",
        sender: 'assistant',
        timestamp: new Date(),
        type: 'error',
      };
      setMessages(prev => [...prev, message]);

      // simulate event
      simulateEvents(handleEvent);
        
      return;
    }

    sendQuery(inputValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isModelResponding) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const downloadReport = (content: any) => {
    try {
      const data = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
      
      // Determine file extension based on content
      const isHtml = /^\s*</.test(data);
      const fileExtension = isHtml ? '.html' : '.txt';
      const mimeType = isHtml ? 'text/html' : 'text/plain';

      const blob = new Blob([data], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${new Date().toISOString().slice(0, 10)}${fileExtension}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  // Handle scroll events to detect user's scroll position
  const handleScroll = useCallback(() => {
    if (!mainContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    const isAtBottom = scrollHeight - (scrollTop + clientHeight) < 100; // 100px threshold
    
    if (isAtBottom !== isUserAtBottom) {
      setIsUserAtBottom(isAtBottom);
      console.log('isAtBottom', isAtBottom);
    }
  }, [isUserAtBottom]);

  // Add scroll event listener to window
  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  const scrollToBottom = () => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    });
  };

  // Auto-scroll to bottom when messages change and user is at bottom
  useEffect(() => {
    if (isUserAtBottom) {
      scrollToBottom();
    }
  }, [messages, isUserAtBottom]);

  // Function to scroll to a specific message
  const scrollToMessage = useCallback((id: number) => {
    const messageElement = document.getElementById(`message-${id}`);
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Add highlight effect
      messageElement.classList.add('highlight-message');
      setTimeout(() => {
        messageElement.classList.remove('highlight-message');
      }, 2000);
    }
  }, []);

  const handleOpenSettings = () => setSettingsOpen(true);
  const handleCloseSettings = () => setSettingsOpen(false);
  
  const handleSaveSettings = () => {
    localStorage.setItem('wsUrl', wsUrl);
    handleCloseSettings();
    // Reload the page to reconnect with the new WebSocket URL
    window.location.reload();
  };

  return (
    <div className="app">
      <button 
        className="settings-button"
        onClick={handleOpenSettings}
        title="Settings"
      >
        <i className="fas fa-cog"></i>
      </button>
      
      {settingsOpen && (
        <div className="modal-overlay" onClick={handleCloseSettings}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3>Settings</h3>
            <div className="form-group">
              <label htmlFor="wsUrl">WebSocket URL</label>
              <input
                id="wsUrl"
                type="text"
                value={wsUrl}
                onChange={(e) => setWsUrl(e.target.value)}
                placeholder="ws://localhost:8848/ws"
              />
            </div>
            <div className="modal-actions">
              <button onClick={handleCloseSettings}>Cancel</button>
              <button onClick={handleSaveSettings} className="primary">Save</button>
            </div>
          </div>
        </div>
      )}
      
      <div className="main-content">
        <div className="chat-container" ref={mainContainerRef}>
          <div className="header-container">
            <h1 className="chat-title"><img className="title-logo" src={logoSquareUrl} alt="logo" />Youtu Agent</h1>
            
          </div>

          <div className="chat-messages">
            {messages.map((message, index) => {
              // Check if previous message is from the same sender
              const showSender = index === 0 ||
                messages[index - 1].sender !== message.sender ||
                message.sender === 'user';

              return (
                <div key={message.id} id={`message-${message.id}`}>
                  <MessageComponent
                    message={message}
                    showSender={showSender}
                    onDownloadReport={message.type === 'report' ? (content) => {
                      downloadReport(content);
                    } : undefined}
                  />
                </div>
              );
            })}
            
            {isModelResponding && (
              <div className="respond-placeholder">
                <i className="breathing-circle fa fa-circle"></i>
              </div>
            )}
            
            {!hideExampleQuery && exampleQuery.length > 0 && (
              <div className="example-queries">
                <div className="example-queries-title">Try asking:</div>
                {exampleQuery.map((query, idx) => (
                  <div key={idx} className="example-query" onClick={() => {
                    setInputValue(query);
                    setHideExampleQuery(true);
                  }}>
                    {query}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {/* Agent TOC */}
          <AgentTOC 
            messages={messages} 
            onNavigate={scrollToMessage} 
          />

          <div className="chat-input-container">
            <div className="chat-input-wrapper">
              <div className="input-group">
                <input
                  ref={inputRef}
                  type="text"
                  className="chat-input"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isModelResponding ? 'AI is thinking...' : 'Type a message...'}
                  disabled={isModelResponding}
                />
                <button
                  className="send-button"
                  onClick={handleSendMessage}
                  disabled={isModelResponding}
                  title={isModelResponding ? 'AI is thinking...' : 'Send message'}
                >
                  {isModelResponding ? (
                    <i className="breathing-circle fa fa-circle"></i>
                  ) : (
                    <i className="fas fa-paper-plane"></i>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Footer with pic.png */}
          <footer className="app-footer">
            <div className="p-4">
              <img src={logoUrl} alt="Footer Logo" className="footer-logo" />
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
};

export default App;
