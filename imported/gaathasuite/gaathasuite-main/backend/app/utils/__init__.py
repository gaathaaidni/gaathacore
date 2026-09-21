"""
Common utilities and helpers for the Gaatha Suite application.
"""
import math
from typing import List, Dict, Any, Optional
from datetime import datetime


def calculate_pages(total: int, limit: int) -> int:
    """Calculate number of pages for pagination."""
    return math.ceil(total / limit) if total > 0 else 1


def format_pagination(
    items: List[Any],
    total: int,
    page: int,
    limit: int
) -> Dict[str, Any]:
    """Format pagination metadata."""
    return {
        'data': items,
        'total': total,
        'page': page,
        'limit': limit,
        'pages': calculate_pages(total, limit),
    }


def sanitize_search(search_term: str, max_length: int = 100) -> str:
    """Sanitize search term to prevent injection."""
    if not search_term:
        return ''
    return search_term.strip()[:max_length]


def validate_page_and_limit(page: int, limit: int) -> tuple:
    """Validate pagination parameters."""
    page = max(1, int(page))
    limit = max(1, min(int(limit), 500))  # Cap at 500
    return page, limit


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO format string."""
    if dt is None:
        return None
    return dt.isoformat()


def get_client_ip(request) -> str:
    """Get client IP address from request."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


def calculate_days_remaining(target_date: datetime) -> int:
    """Calculate days remaining until target date."""
    if target_date is None:
        return None
    delta = target_date - datetime.utcnow()
    return delta.days
