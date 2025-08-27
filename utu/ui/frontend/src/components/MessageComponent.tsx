import React, { useState, useEffect } from 'react';
import SafeMarkdown from './SafeMarkdown';
import type { Message, ToolCallMessage } from '../types/message';
import type { PlanItem } from '../types/events';

interface MessageComponentProps {
  message: Message;
  showSender: boolean;
  onDownloadReport?: (content: any) => void;
}

const MessageComponent: React.FC<MessageComponentProps> = ({ 
  message, 
  showSender,
  onDownloadReport 
}) => {
  // Render message sender
  const renderSender = () => {
    if (!showSender) return null;
    return (
      <div className="message-sender">
        {message.sender === 'assistant' ? 'Assistant' : 'You'}
      </div>
    );
  };

  // Render error message
  const renderError = () => (
    <div className="error-content">
      <i className="fas fa-exclamation-circle"></i> {message.content as string}
    </div>
  );

  // Get tool call status text
  const getToolCallStatus = () => {
    const toolName = typeof message.content === 'object' && 'toolName' in message.content 
      ? ` [${message.content.toolName}]` 
      : '';
    return message.inprogress ? `Tool Calling${toolName}` : `Tool Called${toolName}`;
  };

  // Render tool call details
  const renderToolCall = () => {
    if (typeof message.content !== 'object' || !('toolCallArgument' in message.content)) {
      return null;
    }

    let displayContent = message.content.toolCallArgument;

    let isCode = false;
    
    try {
      // Try to parse the toolCallArgument as JSON
      const parsed = JSON.parse(message.content.toolCallArgument);
      // If it's an object with exactly one key, use its value
      if (parsed && typeof parsed === 'object' && Object.keys(parsed).length === 1) {
        const firstKey = Object.keys(parsed)[0];
        displayContent = typeof parsed[firstKey] === 'string' 
          ? parsed[firstKey] 
          : JSON.stringify(parsed[firstKey], null, 2);
      }
      if (parsed && typeof parsed === 'object' && parsed["code"]) {
        displayContent = parsed["code"];
        isCode = true;
      }
    } catch (e) {
      // If parsing fails, use the original content
      console.log('Not a JSON string, using original content');
    }

    return (
      <>
        {displayContent && (
          <div className="tool-call-argument">
            {/* <h4>Arguments:</h4> */}
            {isCode ? <pre>{displayContent}</pre> : displayContent}
          </div>
        )}
        {/* {message.content.toolCallOutput && (
          <div className="tool-call-output">
            <h4>Output:</h4>
            <SafeMarkdown>{message.content.toolCallOutput}</SafeMarkdown>
          </div>
        )} */}
      </>
    );
  };

  // Get status text
  const getStatusText = () => {
    if (message.inprogress) {
      if (message.type === 'reason') return 'Thinking';
      if (message.type === 'worker') return 'Working';
      if (message.type === 'report') return 'Reporting';
      if (message.type === 'plan') return 'Planning';
      if (message.type === 'new_agent') return 'Initializing Agent';
      return 'Processing';
    } else {
      if (message.type === 'reason') return 'Thought';
      if (message.type === 'worker') return 'Worker';
      if (message.type === 'report') return 'Report';
      if (message.type === 'plan') return 'Plan';
      if (message.type === 'new_agent') return 'Agent';
      return String(message.type);
    }
  };

  // Render download button
  const renderDownloadButton = () => {
    if (message.type !== 'report' || !onDownloadReport) return null;
    
    return (
      <button
        className="download-button"
        onClick={(e) => {
          e.stopPropagation();
          onDownloadReport(message.content);
        }}
        title="Download Report"
      >
        <i className="fas fa-download"></i>
      </button>
    );
  };

  // Render plan content
  const renderPlanContent = (plan: PlanItem) => (
    <div className="plan-content">
      <div className="plan-analysis">
        <SafeMarkdown>{plan.analysis}</SafeMarkdown>
      </div>
      {plan.todo.length > 0 && (
        <div className="plan-todo">
          <h4>Todo:</h4>
          <ol className="todo-list">
            {plan.todo.map((item, index) => (
              <li key={index} className="todo-item">
                <SafeMarkdown>{item}</SafeMarkdown>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );

  // Render agent content
  const renderAgentContent = (agentName: string) => (
    <div className="agent-content">
      <div className="agent-name">
        <i className="fas fa-robot"></i> {agentName}
      </div>
      <div className="agent-status">
        {message.inprogress ? 'Initializing...' : 'Ready'}
      </div>
    </div>
  );

  const renderReportContent = (content: string) => {
    // Remove 'report: ' prefix if it exists
    let reportContent = content.startsWith('report: ')
      ? content.substring(8)
      : content;

    // Basic check for HTML content by looking for a starting tag
    const isSVG = /<svg(.*)<\/svg>/s.test(reportContent);
    let isHtml = /^\s*</.test(reportContent);

    console.log("ishtml, isSVG", isHtml, isSVG);

    if (!isHtml && /^\s*```html/s.test(reportContent)) {
      const match = reportContent.match(/```html(.*)```/s);
      if (match) {
        reportContent = match[1];
      }
      isHtml = true;
      console.log("ishtml!!!!");
      console.log(reportContent);
    }

    if (isSVG) {
      const match = reportContent.match(/<svg(.*)<\/svg>/s);
      if (match) {
        reportContent = "<svg" + match[1] + "</svg>";
      }
      return (
        <div className="report-svg" dangerouslySetInnerHTML={{ __html: reportContent }} />
      );
    }

    if (isHtml) {
      const resetStyles = `
        <style>
          * {
            all: revert;
            box-sizing: border-box;
          }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
            line-height: 1.5;
            margin: 0;
            padding: 1rem;
            color: #333;
            background: white;
          }
        </style>
      `;

      return (
        <iframe
          srcDoc={`<!DOCTYPE html><html><head>${resetStyles}</head><body>${reportContent}</body></html>`}
          className="report-iframe"
          style={{ 
            width: '100%', 
            border: '1px solid #e0e0e0',
            borderRadius: '8px',
            minHeight: '400px',
            backgroundColor: 'white',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}
          sandbox="allow-same-origin"
          loading="lazy"
        />
      );
    }

    return <SafeMarkdown>{reportContent}</SafeMarkdown>;
  };

  const renderMessageContent = () => {
    // Error message
    if (message.type === 'error') {
      return renderError();
    }
    
    // User message - render as plain text without markdown
    if (message.sender === 'user') {
      return <div className="user-message">{String(message.content)}</div>;
    }
    
    // Report message - render in details/summary with code block content
    if (message.type === 'report') {
      const handleDownload = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (onDownloadReport) {
          // Remove 'report: ' prefix if it exists before downloading
          const content = String(message.content).startsWith('report: ')
            ? String(message.content).substring(8)
            : String(message.content);
          onDownloadReport(content);
        }
      };

      const handleOpenInNewTab = (e: React.MouseEvent) => {
        e.stopPropagation();
        let reportContent = String(message.content).startsWith('report: ')
            ? String(message.content).substring(8)
            : String(message.content);

        let isHtml = /^\s*</.test(reportContent);
        if (!isHtml && /^\s*```html/s.test(reportContent)) {
          const match = reportContent.match(/```html(.*)```/s);
          if (match) {
            reportContent = match[1];
          }
          isHtml = true;
        }

        const newWindow = window.open();
        if (newWindow) {
            if (isHtml) {
                newWindow.document.write(reportContent);
            } else {
                newWindow.document.write(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Report</title>
                        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
                        <style>
                            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 2rem; }
                            table {
                              border-collapse: collapse;
                              width: 100%;
                              margin: 1em 0;
                              font-size: 0.9em;
                              /* box-shadow: 0 0 20px rgba(0, 0, 0, 0.1); */
                              overflow-x: scroll;
                              border-radius: 5px;
                            }

                            th,
                            td {
                              padding: 12px 15px;
                              text-align: left;
                              border: 1px solid #e0e0e0;
                            }

                            thead tr {
                              background-color: #f5f5f5;
                              color: var(--color-header-text);
                              text-align: left;
                              font-weight: bold;
                            }

                            tbody tr {
                              border-bottom: 1px solid #e0e0e0;
                            }

                            tbody tr:nth-of-type(even) {
                              background-color: #f8f8f8;
                            }

                            tbody tr:last-of-type {
                              border-bottom: 2px solid var(--color-header-bg);
                            }

                            tbody tr:hover {
                              background-color: var(--color-row-hover);
                            }
                        </style>
                    </head>
                    <body>
                        <div id="content"></div>
                        <script>
                            document.getElementById('content').innerHTML = marked.parse(${JSON.stringify(reportContent)});
                        </script>
                    </body>
                    </html>
                `);
            }
            newWindow.document.close();
        }
      };

      return (
        <details className="message-detail" open>
          <summary className="message-detail-summary">
            <span>Report</span>
            <button
              className="download-button"
              onClick={handleOpenInNewTab}
              title="Open in new tab"
            >
              <i className="fas fa-external-link-alt"></i>
            </button>
            <button
              className="download-button"
              onClick={handleDownload}
              title="Download Report"
            >
              <i className="fas fa-download"></i>
            </button>
          </summary>
          <div className="message-detail-content">
            {renderReportContent(String(message.content))}
          </div>
        </details>
      );
    }
    
    // Agent message
    if (message.type === 'new_agent' && typeof message.content === 'string') {
      return (
        <div className="agent-message">
          {renderAgentContent(message.content)}
        </div>
      );
    }
    
    // Plan message
    if (message.type === 'plan' && typeof message.content === 'object' && 'analysis' in message.content) {
      return (
        <details className="message-detail plan-message" open>
          <summary className="message-detail-summary">
            <span>{getStatusText()}</span>
          </summary>
          <div className="message-detail-content">
            {renderPlanContent(message.content as PlanItem)}
          </div>
        </details>
      );
    }
  
    // Tool call message
    if (message.type === 'tool_call') {
      let icon = "🖥️";
      if ((message.content as ToolCallMessage).toolName == "web_qa") {
        icon = "🌐";
      } else if ((message.content as ToolCallMessage).toolName == "document_qa") {
        icon = "📖";
      } else if ((message.content as ToolCallMessage).toolName == "search_google_api") {
        icon = "🔍";
      }
      return (
        <details className="message-detail tool-call-message" open>
          <summary
            className="message-detail-summary"
            {...(message.inprogress ? { 'data-inprogress': 'true' } : {})}
          >
            <span>{getToolCallStatus()}</span> {icon}
          </summary>
          <div className="message-detail-content">
            {renderToolCall()}
          </div>
        </details>
      );
    }
    
    // Other special type message
    if (message.type && message.type !== 'text') {
      return (
        <details className="message-detail">
          <summary
            className="message-detail-summary"
            {...(message.inprogress ? { 'data-inprogress': 'true' } : {})}
          >
            <span>{getStatusText()}</span>
            {renderDownloadButton()}
          </summary>
          <div className="message-detail-content">
            <SafeMarkdown>{String(message.content)}</SafeMarkdown>
          </div>
        </details>
      );
    }
    
    // Text message
    return <SafeMarkdown>{String(message.content)}</SafeMarkdown>;
  };

  const [confirmedStatus, setConfirmedStatus] = useState<'confirmed' | 'rejected' | undefined>(message.confirmedStatus);

  // Update local state if message.confirmedStatus changes from parent
  useEffect(() => {
    setConfirmedStatus(message.confirmedStatus);
  }, [message.confirmedStatus]);

  const handleConfirm = () => {
    console.log('Confirmed message:', message.id);
    setConfirmedStatus('confirmed');
    // You can also emit an event to parent component here if needed
  };

  const handleCancel = () => {
    console.log('Rejected message:', message.id);
    setConfirmedStatus('rejected');
    // You can add cancellation logic here if needed
  };

  // Check message confirmation status
  const isConfirmed = confirmedStatus === 'confirmed';
  const isRejected = confirmedStatus === 'rejected';
  const showConfirmStatus = message.requireConfirm && (isConfirmed || isRejected);
  const showConfirmButtons = message.requireConfirm && !showConfirmStatus;
  const showConfirmClass = message.requireConfirm && !isConfirmed && !isRejected;

  return (
    <div
      key={message.id}
      className={`message ${message.sender === 'user' ? 'message-user' : 'message-bot'}`}
    >
      {renderSender()}
      <div className={`message-content ${message.type === 'error' ? 'error-message' : ''} ${showConfirmClass ? 'message-requires-confirm' : ''} ${isConfirmed ? 'message-confirmed' : ''} ${isRejected ? 'message-rejected' : ''}`}>
        {renderMessageContent()}
        {(showConfirmButtons || showConfirmStatus) && (
          <div className="confirmation-buttons">
            <ActionButtons
              onConfirm={handleConfirm}
              onCancel={handleCancel}
              confirmText="Confirm"
              cancelText="Reject"
              showConfirmStatus={isConfirmed ? 'confirmed' : isRejected ? 'rejected' : undefined}
            />
          </div>
        )}
      </div>
    </div>
  );
};

interface ActionButtonsProps {
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  className?: string;
  showConfirmStatus?: 'confirmed' | 'rejected';
}

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  className = '',
  showConfirmStatus = false
}) => {
  if (showConfirmStatus === 'confirmed') {
    return (
      <div className="confirmation-status" style={{ color: '#4CAF50', fontSize: '0.9em' }}>
        <i className="fas fa-check-circle"></i> Confirmed
      </div>
    );
  }
  
  if (showConfirmStatus === 'rejected') {
    return (
      <div className="confirmation-status" style={{ color: '#f44336', fontSize: '0.9em' }}>
        <i className="fas fa-times-circle"></i> Rejected
      </div>
    );
  }

  return (
    <div className={`action-buttons-container ${className}`}>
      <button
        onClick={onConfirm}
        className="action-button action-button--primary"
      >
        <i className="fas fa-check"></i>
        <span>{confirmText}</span>
      </button>
      <button
        onClick={onCancel}
        className="action-button action-button--secondary"
      >
        <i className="fas fa-times"></i>
        <span>{cancelText}</span>
      </button>
    </div>
  );
};

export default MessageComponent;
