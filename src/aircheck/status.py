import datetime
from enum import Enum
from typing import Optional, Tuple


class Status(str, Enum):
    MATCH = "MATCH"
    NOT_MATCHING = "NOT_MATCHING"
    SILENCE_ON_OFF_AIR = "SILENCE_ON_OFF_AIR"
    SILENCE_ON_PROGRAM = "SILENCE_ON_PROGRAM"
    SILENCE_ON_BOTH = "SILENCE_ON_BOTH"
    UNCERTAIN = "UNCERTAIN"


def determine_status(
    off_air_rms: float,
    program_rms: float,
    similarity: Optional[float],
    delay_ms: Optional[float],
    min_rms: float,
    match_threshold: float,
    max_delay_ms: float,
) -> Tuple[Status, str]:
    """
    Pure function: maps audio measurements to a Status value and a detail string.
    Keeping this separate from I/O makes it straightforward to add alert hooks later.
    """
    # Silence checks take priority — no point running cross-correlation on silence
    if off_air_rms < min_rms and program_rms < min_rms:
        return Status.SILENCE_ON_BOTH, ""
    if off_air_rms < min_rms:
        return Status.SILENCE_ON_OFF_AIR, ""
    if program_rms < min_rms:
        return Status.SILENCE_ON_PROGRAM, ""

    # Both feeds have audio but comparison result is not available
    if similarity is None or delay_ms is None:
        return Status.UNCERTAIN, "comparison error"

    score_str = f"score={similarity:.3f} delay={delay_ms:+.0f}ms"

    if similarity >= match_threshold:
        if abs(delay_ms) <= max_delay_ms:
            return Status.MATCH, score_str
        # Same audio but delay is suspiciously large — flag it rather than MATCH
        return Status.UNCERTAIN, f"{score_str} (delay exceeds limit)"

    return Status.NOT_MATCHING, score_str


def print_status(status: Status, detail: str = "") -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {status.value}"
    if detail:
        line += f"  {detail}"
    print(line, flush=True)
