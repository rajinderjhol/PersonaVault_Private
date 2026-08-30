import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';

interface TimeFilterProps {
  onFilterChange: (startDate: string, endDate: string, range: string) => void;
  initialRange?: string;
}

export const TimeFilter: React.FC<TimeFilterProps> = ({ 
  onFilterChange, 
  initialRange = '30d' 
}) => {
  const [selectedRange, setSelectedRange] = useState<string>(initialRange);

  const setRange = (range: string, start?: Date, end?: Date) => {
    setSelectedRange(range);
    const now = new Date();
    let startDate = start || new Date();
    let endDate = end || now;

    if (!start || !end) {
        if (range === 'today') {
            startDate = new Date(now.setHours(0, 0, 0, 0));
            endDate = new Date();
        } else if (range === '7d') {
            startDate = new Date(now.setDate(now.getDate() - 7));
        } else if (range === '30d') {
            startDate = new Date(now.setDate(now.getDate() - 30));
        } else if (range === '90d') {
            startDate = new Date(now.setDate(now.getDate() - 90));
        }
    }
    
    onFilterChange(
        format(startDate, 'yyyy-MM-dd'),
        format(endDate, 'yyyy-MM-dd'),
        range
    );
  };

  return (
    <div className="time-filter-container">
      <div className="preset-buttons">
        {['today', '7d', '30d', '90d'].map(range => (
          <button
            key={range}
            className={`preset-btn ${selectedRange === range ? 'active' : ''}`}
            onClick={() => setRange(range)}
          >
            {range.toUpperCase()}
          </button>
        ))}
        {/* Custom implementation would go here */}
      </div>
    </div>
  );
};
