"""Recurrence pattern calculator using dateutil.rrule.

Per T064: Implements recurrence pattern calculation for:
- Daily: Every N days
- Weekly: Every N weeks on specific days
- Monthly: Every N months on specific day
- Custom: RFC 5545 RRULE strings
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from dateutil.rrule import (
    DAILY,
    MONTHLY,
    WEEKLY,
    rrule,
    rrulestr,
    MO, TU, WE, TH, FR, SA, SU,
)
from pydantic import BaseModel


class RecurrenceFrequency(str, Enum):
    """Recurrence frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class RecurrencePattern(BaseModel):
    """Recurrence pattern data from task event."""
    id: str
    frequency: RecurrenceFrequency
    interval: int = 1
    by_weekday: Optional[list[int]] = None  # 0=Mon, 6=Sun
    by_monthday: Optional[int] = None  # 1-31
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    rrule_string: Optional[str] = None


# Map weekday index (0=Mon) to dateutil weekday
WEEKDAY_MAP = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA, 6: SU}


def calculate_next_occurrence(
    pattern: RecurrencePattern,
    last_completed: datetime,
    occurrences_count: int = 0,
) -> Optional[datetime]:
    """Calculate the next occurrence date for a recurring task.

    Args:
        pattern: The recurrence pattern configuration
        last_completed: When the last instance was completed
        occurrences_count: How many instances have been created so far

    Returns:
        Next occurrence datetime, or None if recurrence has ended

    Per T069: Handles end conditions (end_date, max_occurrences)
    """
    # Check if max occurrences reached
    if pattern.max_occurrences and occurrences_count >= pattern.max_occurrences:
        return None

    # Use custom RRULE string if provided
    if pattern.frequency == RecurrenceFrequency.CUSTOM and pattern.rrule_string:
        return _calculate_from_rrule_string(
            pattern.rrule_string,
            last_completed,
            pattern.end_date,
        )

    # Calculate based on frequency type
    next_date = _calculate_standard_occurrence(pattern, last_completed)

    # Check if past end date
    if pattern.end_date and next_date and next_date > pattern.end_date:
        return None

    return next_date


def _calculate_standard_occurrence(
    pattern: RecurrencePattern,
    after: datetime,
) -> Optional[datetime]:
    """Calculate next occurrence for standard frequency types."""

    if pattern.frequency == RecurrenceFrequency.DAILY:
        # Every N days
        rule = rrule(
            DAILY,
            interval=pattern.interval,
            dtstart=after,
            count=2,  # Get first occurrence after 'after'
        )

    elif pattern.frequency == RecurrenceFrequency.WEEKLY:
        # Every N weeks on specific days
        byweekday = None
        if pattern.by_weekday:
            byweekday = [WEEKDAY_MAP[d] for d in pattern.by_weekday if d in WEEKDAY_MAP]

        rule = rrule(
            WEEKLY,
            interval=pattern.interval,
            byweekday=byweekday,
            dtstart=after,
            count=2,
        )

    elif pattern.frequency == RecurrenceFrequency.MONTHLY:
        # Every N months on specific day
        rule = rrule(
            MONTHLY,
            interval=pattern.interval,
            bymonthday=pattern.by_monthday or after.day,
            dtstart=after,
            count=2,
        )
    else:
        return None

    # Get all occurrences and find the first one strictly after 'after'
    occurrences = list(rule)
    for occ in occurrences:
        if occ > after:
            return occ

    return None


def _calculate_from_rrule_string(
    rrule_str: str,
    after: datetime,
    end_date: Optional[datetime] = None,
) -> Optional[datetime]:
    """Parse RFC 5545 RRULE string and get next occurrence.

    Per T064: Supports custom patterns via RFC 5545 RRULE.
    """
    try:
        # Parse the RRULE string
        rule = rrulestr(rrule_str, dtstart=after)

        # Get next occurrence after the given date
        next_occ = rule.after(after)

        if next_occ is None:
            return None

        # Check end date
        if end_date and next_occ > end_date:
            return None

        return next_occ

    except (ValueError, TypeError) as e:
        # Invalid RRULE string
        return None


def calculate_due_date_for_instance(
    original_due_date: Optional[datetime],
    original_completed: datetime,
    next_occurrence: datetime,
) -> Optional[datetime]:
    """Calculate due date for the new task instance.

    If the original task had a due date, the new instance should have
    a due date that maintains the same relative offset.
    """
    if not original_due_date:
        return None

    # Calculate offset between original due date and when it was completed
    # (could be completed before or after due date)
    offset = original_due_date - original_completed

    # Apply same offset to new occurrence
    return next_occurrence + offset
