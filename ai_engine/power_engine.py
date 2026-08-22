#!/usr/bin/env python3
"""Power optimization policy engine for AstraOS."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict


@dataclass
class PowerState:
    battery_percent: int
    discharge_watts: float
    cpu_governor: str
    screen_watts: float
    inference_active: bool


def recommend(state: PowerState) -> dict:
    actions = []
    if state.battery_percent < 35 and state.discharge_watts > 18:
        actions.append("switch_background_cores_to_powersave")
    if state.inference_active and state.discharge_watts > 24:
        actions.append("offload_inference_to_edge_node")
    if state.screen_watts > 5:
        actions.append("reduce_refresh_rate_during_background_training")
    if not actions:
        actions.append("maintain_balanced_governor")
    return {"projected_savings_watts": round(len(actions) * 2.4, 2), "actions": actions}


def main() -> None:
    state = PowerState(31, 26.4, "performance", 6.2, True)
    print(json.dumps({"power": asdict(state), "recommendation": recommend(state)}, indent=2))


if __name__ == "__main__":
    main()
