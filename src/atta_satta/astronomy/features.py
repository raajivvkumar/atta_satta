"""Experimental, reproducible astronomy features.

Astronomical features are optional and are never treated as causal evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AstronomyFeatures:
    timestamp_utc: datetime
    sun_ecliptic_longitude: float | None
    moon_ecliptic_longitude: float | None
    lunar_phase_degrees: float | None


def calculate_features(timestamp_utc: datetime) -> AstronomyFeatures:
    """Calculate basic celestial features using Skyfield when installed.

    The function deliberately returns no fabricated values when the optional
    astronomy dependency/data is unavailable.
    """
    if timestamp_utc.tzinfo is None:
        raise ValueError("timestamp_utc must be timezone-aware")

    try:
        from skyfield.api import load
        from skyfield.framelib import ecliptic_frame
    except ImportError as exc:
        raise RuntimeError(
            "Astronomy features require the optional 'astronomy' dependency."
        ) from exc

    ts = load.timescale()
    eph = load("de421.bsp")
    t = ts.from_datetime(timestamp_utc)
    earth = eph["earth"]
    sun = eph["sun"]
    moon = eph["moon"]
    sun_position = earth.at(t).observe(sun).apparent().frame_latlon(ecliptic_frame)[1].degrees
    moon_position = earth.at(t).observe(moon).apparent().frame_latlon(ecliptic_frame)[1].degrees
    phase = (moon_position - sun_position) % 360.0
    return AstronomyFeatures(
        timestamp_utc=timestamp_utc,
        sun_ecliptic_longitude=sun_position,
        moon_ecliptic_longitude=moon_position,
        lunar_phase_degrees=phase,
    )
