import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tyre.fitter import WLSFitter, isolate_response_variable, compute_age_weights, compute_huber_weights
