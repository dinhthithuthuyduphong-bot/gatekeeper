"""Gatekeeper: risk-controlled admission of learned coding skills.

Core, LLM-free components (TODO.md, Phase 5a):

* :mod:`gatekeeper.eprocess` - betting e-process for the null STR(S, s) > -theta.
* :mod:`gatekeeper.alpha_ledger` - pre-allocated alpha budget (cells, composites, re-admission).
* :mod:`gatekeeper.simulate` - Monte-Carlo checks of admission rate, trial count and type-I error.
* :mod:`gatekeeper.composition_example` - executable counterexample behind Theorem 7.
"""

from gatekeeper.alpha_ledger import AlphaLedger
from gatekeeper.eprocess import AdmissionResult, BettingEProcess, run_admission

__all__ = ["AdmissionResult", "AlphaLedger", "BettingEProcess", "run_admission"]
__version__ = "0.1.0"
