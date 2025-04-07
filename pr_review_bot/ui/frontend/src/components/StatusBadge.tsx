import React from 'react';

type StatusType = 'success' | 'warning' | 'error' | 'info';

interface StatusBadgeProps {
  status: StatusType | string;
  text: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, text }) => {
  let bgColor = '';
  let textColor = 'text-white';
  let icon = '';

  switch (status) {
    case 'success':
    case 'Healthy':
      bgColor = 'bg-success';
      icon = '✓';
      break;
    case 'warning':
      bgColor = 'bg-warning';
      icon = '⚠️';
      break;
    case 'error':
    case 'No commits':
      bgColor = 'bg-error';
      icon = '✗';
      break;
    case 'info':
    case 'Running':
      bgColor = 'bg-primary';
      icon = '✓';
      break;
    default:
      if (status.includes('error') || status.includes('Error')) {
        bgColor = 'bg-warning';
        icon = '⚠️';
      } else if (status.includes('PR') || status.includes('Open')) {
        bgColor = 'bg-primary';
        icon = '';
      } else if (status.includes('Merged')) {
        bgColor = 'bg-success';
        icon = '';
      } else {
        bgColor = 'bg-gray-500';
        icon = '';
      }
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${bgColor} ${textColor}`}>
      {icon && <span className="mr-1">{icon}</span>}
      {text}
    </span>
  );
};

export default StatusBadge;