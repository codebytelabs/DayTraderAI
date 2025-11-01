
import React, { useState, useEffect, useRef } from 'react';

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  isPositive: boolean;
}

const ArrowUpIcon: React.FC = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
    </svg>
);

const ArrowDownIcon: React.FC = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-3.707-9.293a1 1 0 001.414 1.414L9 10.586V7a1 1 0 102 0v3.586l1.293-1.293a1 1 0 10-1.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 101.414 1.414L6.293 10H10a1 1 0 100-2H6.293l.293-.293z" clipRule="evenodd" />
    </svg>
);


export const StatCard: React.FC<StatCardProps> = ({ title, value, change, isPositive }) => {
  const changeColor = isPositive ? 'text-brand-success' : 'text-brand-danger';
  const [isAnimating, setIsAnimating] = useState(false);
  const prevValueRef = useRef(value);

  useEffect(() => {
    if (prevValueRef.current !== value) {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), 500);
      prevValueRef.current = value;
      return () => clearTimeout(timer);
    }
  }, [value]);

  return (
    <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2 transition-transform duration-300 transform hover:-translate-y-1">
      <h3 className="text-sm font-medium text-brand-text-secondary mb-1">{title}</h3>
      <p className={`text-2xl font-semibold text-brand-text transition-all duration-500 ${isAnimating ? 'animate-pulse' : ''}`}>{value}</p>
      {change && (
        <div className={`flex items-center text-sm mt-1 ${changeColor}`}>
          {isPositive ? <ArrowUpIcon /> : <ArrowDownIcon />}
          <span className="ml-1 font-medium">{change}</span>
        </div>
      )}
    </div>
  );
};
