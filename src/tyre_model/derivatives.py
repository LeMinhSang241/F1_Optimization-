import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tyre.derivatives import (
    marginal_degradation,
    degradation_acceleration,
    discrete_step_jump,
    closed_form_stint_degradation,
    closed_form_stint_lap_time,
    fix_total_laps
)
