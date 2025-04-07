import React, { ReactNode } from 'react';

interface CardProps {
  title: string;
  children: ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ title, children, className = '' }) => {
  return (
    <div className={`card ${className}`}>
      <h2 className="text-lg font-semibold mb-3 border-b pb-2">{title}</h2>
      <div>{children}</div>
    </div>
  );
};

export default Card;