import React from 'react'
import './Loading.css'

const Loading = ({ message = 'Se incarca...', size = 'medium' }) => {
  return (
    <div className={`loading-container loading-${size}`}>
      <div className="loading-content">
        {/* Minge de fotbal animata */}
        <div className="football-loader">
          <svg 
            viewBox="0 0 100 100" 
            className="football-svg"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Minge de fotbal */}
            <circle 
              cx="50" 
              cy="50" 
              r="40" 
              fill="url(#ballGradient)"
              className="football-circle"
            />
            
            {/* Pattern minge de fotbal */}
            <path 
              d="M 50 10 Q 30 30 20 50 Q 30 70 50 90 Q 70 70 80 50 Q 70 30 50 10" 
              stroke="white" 
              strokeWidth="2" 
              fill="none"
              opacity="0.8"
            />
            <path 
              d="M 10 50 Q 30 30 50 10 Q 70 30 90 50 Q 70 70 50 90 Q 30 70 10 50" 
              stroke="white" 
              strokeWidth="2" 
              fill="none"
              opacity="0.8"
            />
            <path 
              d="M 30 20 Q 50 30 70 20 M 30 80 Q 50 70 70 80" 
              stroke="white" 
              strokeWidth="1.5" 
              fill="none"
              opacity="0.6"
            />
            <path 
              d="M 20 30 Q 30 50 20 70 M 80 30 Q 70 50 80 70" 
              stroke="white" 
              strokeWidth="1.5" 
              fill="none"
              opacity="0.6"
            />
            
            {/* Centru */}
            <circle cx="50" cy="50" r="3" fill="white" opacity="0.9" />
            
            {/* Simbol AI - Neural Network discret */}
            <g className="ai-symbol" opacity="0.6">
              <circle cx="30" cy="30" r="2.5" fill="#ff6b35" />
              <circle cx="50" cy="25" r="2.5" fill="#ff6b35" />
              <circle cx="70" cy="30" r="2.5" fill="#ff6b35" />
              <circle cx="35" cy="50" r="2.5" fill="#ff6b35" />
              <circle cx="65" cy="50" r="2.5" fill="#ff6b35" />
              <line x1="30" y1="30" x2="35" y2="50" stroke="#ff6b35" strokeWidth="1" />
              <line x1="50" y1="25" x2="35" y2="50" stroke="#ff6b35" strokeWidth="1" />
              <line x1="50" y1="25" x2="65" y2="50" stroke="#ff6b35" strokeWidth="1" />
              <line x1="70" y1="30" x2="65" y2="50" stroke="#ff6b35" strokeWidth="1" />
            </g>
            
            <defs>
              <linearGradient id="ballGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#fbbf24" />
                <stop offset="50%" stopColor="#f59e0b" />
                <stop offset="100%" stopColor="#d97706" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        
        {/* Text loading */}
        <div className="loading-text">
          <span className="loading-message">{message}</span>
          <div className="loading-dots">
            <span className="dot dot-1">.</span>
            <span className="dot dot-2">.</span>
            <span className="dot dot-3">.</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Loading

