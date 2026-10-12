# Copyright (c) 2026 Evgeny Gennadievich Prutkov <sviazist.pr@gmail.com>
# SPDX-License-Identifier: MIT
#
# Python implementation of ITU-R P.528-5.
# See README.md and NOTICE for attribution.

"""
p528 — ITU-R P.528-5 (Python port of NTIA reference implementation).

Использование:
    from p528 import p528, Result

    r = p528(d__km=100.0, h_1__meter=30.0, h_2__meter=3000.0,
             f__mhz=300.0, T_pol=1, p=50.0)
    print(r.A__db, r.propagation_mode)
"""

from .p528 import p528, p528_ex
from .types import (
    Result, Terminal, Path, LineOfSightParams, TroposcatterParams,
)
from .constants import (
    SUCCESS,
    POLARIZATION__HORIZONTAL, POLARIZATION__VERTICAL,
    PROP_MODE__NOT_SET, PROP_MODE__LOS,
    PROP_MODE__DIFFRACTION, PROP_MODE__SCATTERING,
    ERROR_VALIDATION__D_KM, ERROR_VALIDATION__H_1,
    ERROR_VALIDATION__H_2, ERROR_VALIDATION__TERM_GEO,
    ERROR_VALIDATION__F_MHZ_LOW, ERROR_VALIDATION__F_MHZ_HIGH,
    ERROR_VALIDATION__PERCENT_LOW, ERROR_VALIDATION__PERCENT_HIGH,
    ERROR_VALIDATION__POLARIZATION, ERROR_HEIGHT_AND_DISTANCE,
    WARNING__DFRAC_TROPO_REGION,
)
from .validation import validate_inputs

__version__ = "0.1.0"

__all__ = [
    "p528", "p528_ex",
    "Result", "Terminal", "Path", "LineOfSightParams",
    "TroposcatterParams",
    "SUCCESS",
    "POLARIZATION__HORIZONTAL", "POLARIZATION__VERTICAL",
    "PROP_MODE__NOT_SET", "PROP_MODE__LOS",
    "PROP_MODE__DIFFRACTION", "PROP_MODE__SCATTERING",
    "ERROR_VALIDATION__D_KM", "ERROR_VALIDATION__H_1",
    "ERROR_VALIDATION__H_2", "ERROR_VALIDATION__TERM_GEO",
    "ERROR_VALIDATION__F_MHZ_LOW", "ERROR_VALIDATION__F_MHZ_HIGH",
    "ERROR_VALIDATION__PERCENT_LOW", "ERROR_VALIDATION__PERCENT_HIGH",
    "ERROR_VALIDATION__POLARIZATION", "ERROR_HEIGHT_AND_DISTANCE",
    "WARNING__DFRAC_TROPO_REGION",
    "validate_inputs",
]
