"""Thermal pacing for long local-inference runs.

This machine is a fanless MacBook Air (M4). Sustained back-to-back
generation drives the GPU into deep thermal throttle — measured decode
speed collapsed from ~19 tok/s to ~0.3 tok/s after roughly eight minutes
of continuous load, and does not recover until the load stops. Inserting a
short cooldown between expensive generation calls keeps the chip out of
that state, trading a little wall-clock for an order of magnitude of
throughput. Disable with EVAL_COOLDOWN_S=0 on hardware with active cooling.
"""

import asyncio
import logging
import os

logger = logging.getLogger("evals.pacing")

COOLDOWN_S = float(os.environ.get("EVAL_COOLDOWN_S", "60"))


async def cooldown(label: str = "") -> None:
    """Pause to let the GPU shed heat between generation calls."""
    if COOLDOWN_S <= 0:
        return
    logger.info("thermal cooldown %.0fs%s", COOLDOWN_S, f" after {label}" if label else "")
    await asyncio.sleep(COOLDOWN_S)
