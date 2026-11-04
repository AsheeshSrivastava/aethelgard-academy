"""Every learner-facing wait, in one place.

Governed by:
- ADR-0016 section 2.6 (Cold Check delay, tunable)
- ADR-0019 (stage review retry, 7 and 30 day rechecks) and its 2026-11-04 test mode amendment

The real durations are the defaults. Test mode sets every wait to zero so a whole
stage can be walked in one sitting; it never changes what is graded.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ColdCheckConfig:
    """Delay marked *tunable* in ADR-0016: the unit Cold Check unlock and every 24-hour retry."""

    delay_hours: int = 24


@dataclass(frozen=True)
class Timing:
    cold_check_hours: int = 24
    recheck_days: Tuple[int, ...] = (7, 30)

    @property
    def cold_check(self) -> ColdCheckConfig:
        return ColdCheckConfig(delay_hours=self.cold_check_hours)


REAL_TIMING = Timing()
TEST_TIMING = Timing(cold_check_hours=0, recheck_days=(0, 0))


def timing_for(test_mode: bool) -> Timing:
    return TEST_TIMING if test_mode else REAL_TIMING
