"""Shared stuff for generating MATSim simulations."""
import datetime
import random
from typing import FrozenSet, Literal, NamedTuple, Optional

# Activity types
ActivityType = Literal["home", "work", "shopping"]


class Facility(NamedTuple):
    """Represents a facility."""

    id: int
    x: float
    y: float
    activity_types: FrozenSet[ActivityType]


def random_time(
    begin: datetime.time, end: datetime.time, step: Optional[datetime.timedelta] = None
) -> datetime.time:
    """Selects a random time within a time range given by [begin, end].

    Args:
        begin: Start of the time range (inclusive).
            This must be a naive `datetime.time` object.
        end: End of the time range (inclusive).
            This must be a naive `datetime.time` object.
        step: If given, the returned time will be a form of `begin + x * step`
            (`x` being a randomly-generated integer).

    Raises:
        ValueError: If either `begin` or `end` has timezone information,
            or if begin > end
    """
    if not isinstance(begin, datetime.time):
        raise TypeError(
            f"begin must be a datetime.time, got {begin!r} (type={type(begin)})"
        )
    if not isinstance(end, datetime.time):
        raise TypeError(f"end must be a datetime.time, got {end!r} (type={type(end)})")
    if step is not None and not isinstance(step, datetime.timedelta):
        raise TypeError(
            f"step must be a datetime.timedelta, got {step!r} (type={type(step)})"
        )

    if begin.tzinfo is not None:
        raise ValueError(f"Begin time must have no timezone (got {begin.tzinfo!r})")
    if end.tzinfo is not None:
        raise ValueError(f"End time must have no timezone (got {end.tzinfo!r})")
    if begin > end:
        raise ValueError(
            f"Begin time must be same or lesser than end time (got begin={begin!r}, end={end!r}"
        )

    today = datetime.date.today()
    dt_begin = datetime.datetime.combine(today, begin)
    dt_end = datetime.datetime.combine(today, end)
    time_range = dt_end - dt_begin
    if step is None:
        dt_result = dt_begin + time_range * random.random()
    else:
        dt_result = dt_begin + step * random.randint(0, time_range // step)
    return dt_result.time()
