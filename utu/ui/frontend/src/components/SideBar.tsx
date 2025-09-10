import React, { useEffect, useRef, useState } from 'react';
import './SideBar.css';
import type { Message } from '../types/message';

interface SideBarProps {
  isOpen: boolean;
  onClose: () => void;
  messages?: Message[];
  onNavigate?: (id: number) => void;
  currentConfig?: string;
  agentType?: 'simple' | 'orchestra' | 'other';
  subAgents?: string[] | null;
  onConfigSelect?: (config: string) => void;
  handleAddConfig?: () => void;
  getConfigList: () => void;
  availableConfigs: string[];
}

// Helper function to convert path to a more readable format
const getFilename = (path: string) => {
  // Remove file extension and path
  const filename = path.split('/').pop() || '';
  const nameWithoutExt = filename.replace(/\.ya?ml$/, '');
  
  // Convert snake_case or kebab-case to Title Case
  return nameWithoutExt
    .split(/[_-]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join('');
};

// Custom tooltip component
const Tooltip = ({ content, children }: { content: string; children: React.ReactNode }) => {
  const [isHovered, setIsHovered] = React.useState(false);
  const [position, setPosition] = React.useState({ top: 0, left: 0 });
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (ref.current && isHovered) {
      const rect = ref.current.getBoundingClientRect();
      setPosition({
        left: rect.right + window.scrollX + 8, // 8px offset from the right edge
        top: rect.top + window.scrollY + (rect.height / 2) // Vertical center
      });
    }
  }, [isHovered]);
  
  return (
    <div 
      ref={ref}
      className="tooltip-container"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {children}
      {isHovered && (
        <div 
          className="tooltip"
          style={{
            left: position.left,
            top: position.top,
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
};

const SideBar: React.FC<SideBarProps> = ({
  isOpen,
  onClose,
  messages = [],
  onNavigate = () => {},
  currentConfig = '',
  agentType = 'simple',
  subAgents = null,
  onConfigSelect = () => {},
  handleAddConfig = () => {},
  getConfigList,
  availableConfigs = []
}) => {
  const sidebarRef = useRef<HTMLDivElement>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  // Load configs only once when component mounts
  useEffect(() => {
    if (availableConfigs.length === 0) {
      getConfigList();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array means this runs once on mount

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    if (window.innerWidth > 768) return; // Only for mobile
    
    const handleClickOutside = (event: MouseEvent) => {
      if (sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  const handleNewChat = () => {
    window.open(window.location.href, '_blank');
  };

  return (
    <div 
      ref={sidebarRef}
      className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}
    >
      <div className="sidebar-content">
        <div className="sidebar-section">
          <button 
            className="sidebar-button primary"
            onClick={handleNewChat}
          >
            <i className="fas fa-plus" />
            New Chat
          </button>
        </div>
        
        <div className="sidebar-divider" />
        
        {/* Agent History Section */}
        <div className="sidebar-section">
          <div className="sidebar-section-title">AGENT HISTORY</div>
          <div className="agent-toc-list">
            {messages.filter(msg => msg.type === 'new_agent' && typeof msg.content === 'string').length > 0 ? (
              messages
                .filter((msg) => msg.type === 'new_agent' && typeof msg.content === 'string')
                .map((msg) => (
                  <div 
                    key={msg.id}
                    className="sidebar-button sidebar-button-text agent-toc-item"
                    onClick={() => onNavigate(Number(msg.id))}
                  >
                    <i className="fas fa-robot" style={{ marginRight: '8px' }}></i>
                    {msg.content as string}
                  </div>
                ))
            ) : (
              <div className="sidebar-button-text" style={{ padding: '8px 16px', color: 'var(--color-subtle-text, #6c757d)' }}>
                No history
              </div>
            )}
          </div>
        </div>

        <div className="sidebar-divider" />
        
        {/* Current Config Section */}
        {currentConfig ? (
          <div className="sidebar-section">
            <div className="sidebar-section-title">CURRENT CONFIG</div>
            <div className="current-config-display">
              <div className="current-config-header">
                <i className="fas fa-check-circle"></i>
                <span className="current-config-title">{getFilename(currentConfig)}</span>
              </div>
              <div className="current-config-path">
              {currentConfig}
            </div>
            {agentType === 'orchestra' && subAgents && subAgents.length > 0 && (
              <div className="sub-agents-section">
                <div className="sub-agents-title">Sub-Agents</div>
                <div className="sub-agents-list">
                  {subAgents.map((agent, index) => (
                    <div key={index} className="sub-agent-item">
                      <span className="sub-agent-name">{agent}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            </div>
            <div 
              className="sidebar-button-text agent-toc-item add-config-button"
              onClick={handleAddConfig}
            >
              <i className="fas fa-plus" style={{ marginRight: '6px' }}></i>
              Add New Config
            </div>
          </div>
        ) : null}
        
        <div className="sidebar-divider" style={{ margin: '12px 0' }} />

        {/* Configs Section */}
        <div className="sidebar-section">
          <div className="sidebar-section-header">
            <div className="sidebar-section-title">AVAILABLE CONFIGS</div>
            <button 
              className={`refresh-button ${isRefreshing ? 'refreshing' : ''}`} 
              onClick={async (e) => {
                e.stopPropagation();
                if (isRefreshing) return;
                
                setIsRefreshing(true);
                try {
                  await getConfigList();
                } finally {
                  // Keep spinning for at least 1 second for better UX
                  setTimeout(() => setIsRefreshing(false), 1000);
                }
              }}
              title="Refresh config list"
              disabled={isRefreshing}
            >
              <i className="fas fa-sync-alt"></i>
            </button>
          </div>
          <div className="config-list">
            {availableConfigs.length > 0 ? (
              <>
                {[...availableConfigs]
                  .sort((a, b) => getFilename(a).localeCompare(getFilename(b)))
                  .map((config) => (
                  <div 
                    key={config}
                    className={`sidebar-button-text config-item ${config === currentConfig ? 'active' : ''}`}
                    onClick={() => onConfigSelect(config)}
                  >
                    <Tooltip content={config}>
                      <div className="config-list-item">
                        <div className="config-icon-container">
                          {config.includes('generated/') ? (
                            <i className="fas fa-robot config-icon" title="自动生成配置"></i>
                          ) : config.includes('examples/') ? (
                            <i className="fas fa-flask config-icon" title="示例配置"></i>
                          ) : null}
                        </div>
                        <span className="config-name">
                          {getFilename(config)}
                        </span>
                      </div>
                    </Tooltip>
                  </div>
                ))}
              </>
            ) : (
              <div className="sidebar-button-text" style={{ padding: '8px 16px', color: 'var(--color-subtle-text, #6c757d)' }}>
                No configs available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SideBar;
