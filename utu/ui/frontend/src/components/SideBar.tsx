import React, { useEffect, useRef } from 'react';
import './SideBar.css';

interface SideBarProps {
  isOpen: boolean;
  onClose: () => void;
}

const SideBar: React.FC<SideBarProps> = ({ isOpen, onClose }) => {
  const sidebarRef = useRef<HTMLDivElement>(null);

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

  return (
    <div 
      ref={sidebarRef}
      className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}
    >
      <div className="sidebar-content">
        <button className="sidebar-button">Button 1</button>
        <button className="sidebar-button">Button 2</button>
        <div className="sidebar-divider" />
        <button className="sidebar-button sidebar-button-text">Button 3</button>
        <button className="sidebar-button sidebar-button-text">Button 4</button>
      </div>
    </div>
  );
};

export default SideBar;
