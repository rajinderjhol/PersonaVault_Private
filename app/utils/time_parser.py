"""
Natural Language Time Parser for Temporal Intelligence
Extracts temporal intervals from user queries and converts them to structured time ranges.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re
from dateutil import parser
from dateutil.relativedelta import relativedelta

class TimeParser:
    """
    Parses natural language time expressions into structured temporal intervals.
    Supports relative time (e.g., "last week", "yesterday") and absolute dates.
    """
    
    # Regex patterns for common temporal expressions
    PATTERNS = {
        'relative_days': r'(?:last|past|previous)\s+(\d+)\s+(day|days?|week|weeks?|month|months?|year|years?)',
        'last_period': r'(?:last|past|previous)\s+(week|month|year|quarter|decade)',
        'current_period': r'(?:this|current)\s+(week|month|year|quarter)',
        'next_period': r'(?:next|coming)\s+(week|month|year|quarter)',
        'today': r'\b(today|now|current day)\b',
        'yesterday': r'\b(yesterday|last day)\b',
        'tomorrow': r'\b(tomorrow|next day)\b',
        'specific_date': r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})',
    }
    
    @classmethod
    def parse(cls, query: str, reference_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Parse a query string for temporal expressions.
        
        Args:
            query: Natural language query
            reference_date: Reference date for relative calculations (defaults to now)
            
        Returns:
            Dict with 'start_date', 'end_date', 'interval_type', 'original_expression' or None
        """
        if not query:
            return None
            
        reference_date = reference_date or datetime.now()
        query_lower = query.lower()
        
        # Try each pattern in priority order
        temporal_info = cls._parse_relative_days(query_lower, reference_date)
        if temporal_info:
            return temporal_info
            
        temporal_info = cls._parse_last_period(query_lower, reference_date)
        if temporal_info:
            return temporal_info
            
        temporal_info = cls._parse_current_period(query_lower, reference_date)
        if temporal_info:
            return temporal_info
            
        temporal_info = cls._parse_next_period(query_lower, reference_date)
        if temporal_info:
            return temporal_info
            
        temporal_info = cls._parse_specific_date(query, reference_date)
        if temporal_info:
            return temporal_info
            
        temporal_info = cls._parse_special_terms(query_lower, reference_date)
        if temporal_info:
            return temporal_info
            
        return None
    
    @classmethod
    def _parse_relative_days(cls, query: str, reference_date: datetime) -> Optional[Dict[str, Any]]:
        """Parse patterns like 'last 7 days', 'past 3 weeks'"""
        match = re.search(cls.PATTERNS['relative_days'], query)
        if match:
            value = int(match.group(1))
            period = match.group(2).lower()
            
            # Convert period to days
            days_map = {
                'day': 1, 'days': 1,
                'week': 7, 'weeks': 7,
                'month': 30, 'months': 30,
                'year': 365, 'years': 365
            }
            days = value * days_map.get(period, 1)
            
            end_date = reference_date
            start_date = reference_date - timedelta(days=days)
            
            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'interval_type': 'relative',
                'original_expression': match.group(0),
                'days_span': days,
                'unit': period
            }
        return None
    
    @classmethod
    def _parse_last_period(cls, query: str, reference_date: datetime) -> Optional[Dict[str, Any]]:
        """Parse patterns like 'last week', 'last month'"""
        match = re.search(cls.PATTERNS['last_period'], query)
        if match:
            period = match.group(1).lower()
            return cls._get_period_dates(period, reference_date, offset=-1)
        return None
    
    @classmethod
    def _parse_current_period(cls, query: str, reference_date: datetime) -> Optional[Dict[str, Any]]:
        """Parse patterns like 'this week', 'this month'"""
        match = re.search(cls.PATTERNS['current_period'], query)
        if match:
            period = match.group(1).lower()
            return cls._get_period_dates(period, reference_date, offset=0)
        return None
    
    @classmethod
    def _parse_next_period(cls, query: str, reference_date: datetime) -> Optional[Dict[str, Any]]:
        """Parse patterns like 'next week', 'next month'"""
        match = re.search(cls.PATTERNS['next_period'], query)
        if match:
            period = match.group(1).lower()
            return cls._get_period_dates(period, reference_date, offset=1)
        return None
    
    @classmethod
    def _get_period_dates(cls, period: str, reference_date: datetime, offset: int) -> Optional[Dict[str, Any]]:
        """Helper to calculate period start/end dates"""
        start_date = None
        end_date = None
        unit = period
        
        if period == 'week':
            start_date = reference_date - timedelta(days=reference_date.weekday()) + timedelta(weeks=offset)
            end_date = start_date + timedelta(days=6)
        elif period == 'month':
            if offset == 0:
                start_date = reference_date.replace(day=1)
                end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
            else:
                start_date = reference_date.replace(day=1) + relativedelta(months=offset)
                end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
        elif period == 'year':
            if offset == 0:
                start_date = reference_date.replace(month=1, day=1)
                end_date = start_date.replace(month=12, day=31)
            else:
                start_date = reference_date.replace(month=1, day=1) + relativedelta(years=offset)
                end_date = start_date.replace(month=12, day=31)
        elif period == 'quarter':
            current_quarter = (reference_date.month - 1) // 3
            start_month = 1 + (current_quarter + offset) * 3
            start_date = reference_date.replace(month=start_month, day=1)
            end_date = (start_date + relativedelta(months=3)) - timedelta(days=1)
        elif period == 'decade':
            if offset == 0:
                decade_start = (reference_date.year // 10) * 10
                start_date = reference_date.replace(year=decade_start, month=1, day=1)
                end_date = start_date.replace(year=decade_start + 9, month=12, day=31)
            else:
                decade_start = (reference_date.year // 10) * 10 + (offset * 10)
                start_date = reference_date.replace(year=decade_start, month=1, day=1)
                end_date = start_date.replace(year=decade_start + 9, month=12, day=31)
        else:
            return None
        
        if start_date and end_date:
            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'interval_type': 'relative',
                'original_expression': f'{offset} {period}',
                'unit': unit
            }
        return None
    
    @classmethod
    def _parse_specific_date(cls, query: str, reference_date: datetime) -> Optional[Dict[str, Any]]:
        """Parse specific dates like '2024-12-25' or '12/25/2024'"""
        try:
            date_match = re.search(cls.PATTERNS['specific_date'], query)
            if date_match:
                date_str = date_match.group(1)
                parsed_date = parser.parse(date_str, fuzzy=True)
                if parsed_date:
                    return {
                        'start_date': parsed_date.isoformat(),
                        'end_date': (parsed_date + timedelta(days=1)).isoformat(),
                        'interval_type': 'absolute',
                        'original_expression': date_str,
                        'unit': 'specific_date'
                    }
        except (ValueError, TypeError):
            pass
        return None
    
    @classmethod
    def _parse_special_terms(cls, query: str, reference_date: datetime) -> Optional[Dict[str, Any]]:
        """Parse special terms like 'today', 'yesterday', 'tomorrow'"""
        if re.search(cls.PATTERNS['today'], query):
            return {
                'start_date': reference_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                'end_date': reference_date.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat(),
                'interval_type': 'relative',
                'original_expression': 'today',
                'unit': 'day'
            }
        elif re.search(cls.PATTERNS['yesterday'], query):
            yesterday = reference_date - timedelta(days=1)
            return {
                'start_date': yesterday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                'end_date': yesterday.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat(),
                'interval_type': 'relative',
                'original_expression': 'yesterday',
                'unit': 'day'
            }
        elif re.search(cls.PATTERNS['tomorrow'], query):
            tomorrow = reference_date + timedelta(days=1)
            return {
                'start_date': tomorrow.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                'end_date': tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat(),
                'interval_type': 'relative',
                'original_expression': 'tomorrow',
                'unit': 'day'
            }
        return None
