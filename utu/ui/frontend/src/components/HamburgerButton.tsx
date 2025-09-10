import React from 'react';

interface HamburgerButtonProps {
  isOpen: boolean;
  onClick: () => void;
}

const HamburgerButton: React.FC<HamburgerButtonProps> = ({ isOpen, onClick }) => {
  return (
    <button 
      className={`hamburger-button ${isOpen ? 'open' : ''}`}
      onClick={onClick}
      aria-label="Toggle menu"
      aria-expanded={isOpen}
    >
      <span className={`hamburger-line ${isOpen ? 'rotate-45' : ''}`}></span>
      <span className={`hamburger-line ${isOpen ? 'opacity-0' : ''}`}></span>
      <span className={`hamburger-line ${isOpen ? '-rotate-45' : ''}`}></span>
    </button>
  );
};

export default HamburgerButton;
