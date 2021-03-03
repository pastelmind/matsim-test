"""Generates variations of Scenario 1 (chessboard-like virtual map) with
different values for # of agents, link capacities, and speed limits.

To execute this module, run:

    python -m scripts.generate_scenario1_variants
"""
import pathlib

from .scenario1_common import generate

# ---- Simulation parameters

ROWS = 10
COLS = 10
BLOCK_SIZE = 250
WORK_FACILITY_RATIO = 0.5

DEFAULT_AGENT_COUNT = 500
DEFAULT_SPEED_LIMIT = 50
DEFAULT_CAPACITY = 300

if __name__ == "__main__":
    base_dir = pathlib.Path(__file__, "../../scenario1").resolve()

    seeds = [
        9150876018444461437,
        10540728611964180105,
        18063122348121924453,
        12425293512567465128,
        8493466832560184431,
    ]
    for agent_count in [500, 1000, 2500, 5000, 10000]:
        for trial, seed in enumerate(seeds):
            generate(
                root_dir=base_dir / f"agents_{agent_count}",
                random_seed=seed,
                rows=ROWS,
                cols=COLS,
                block_size=BLOCK_SIZE,  # meters
                agent_count=agent_count,
                speed_limit=DEFAULT_SPEED_LIMIT / 3.6,  # Conversion from km/h to m/s
                link_capacity=DEFAULT_CAPACITY,  # vehicles/hour
                suffix=f"_trial_{trial + 1}",
                mix_work_and_shopping=False,
                work_facility_ratio=WORK_FACILITY_RATIO,
            )

    seeds = [
        12064403907689837551,
        17694054309643662141,
        15663329033086414807,
        17016328801707495484,
        12562576363757321925,
    ]
    for capacity in [300, 150, 60, 30, 15]:
        for trial, seed in enumerate(seeds):
            generate(
                root_dir=base_dir / f"capacity_{capacity}",
                random_seed=seed,
                rows=ROWS,
                cols=COLS,
                block_size=BLOCK_SIZE,  # meters
                agent_count=DEFAULT_AGENT_COUNT,
                speed_limit=DEFAULT_SPEED_LIMIT / 3.6,  # Conversion from km/h to m/s
                link_capacity=capacity,  # vehicles/hour
                suffix=f"_trial_{trial + 1}",
                mix_work_and_shopping=False,
                work_facility_ratio=WORK_FACILITY_RATIO,
            )

    seeds = [
        5639052030887554621,
        4767784778363634275,
        7249612574632152762,
        8603261193146447983,
        12697522633356477416,
    ]
    for speed_limit in [50, 25, 10, 5, 2.5]:
        for trial, seed in enumerate(seeds):
            generate(
                root_dir=base_dir / f"maxspeed_{speed_limit}",
                random_seed=seed,
                rows=ROWS,
                cols=COLS,
                block_size=BLOCK_SIZE,  # meters
                agent_count=DEFAULT_AGENT_COUNT,
                speed_limit=speed_limit / 3.6,  # Conversion from km/h to m/s
                link_capacity=DEFAULT_CAPACITY,  # vehicles/hour
                suffix=f"_trial_{trial + 1}",
                mix_work_and_shopping=False,
                work_facility_ratio=WORK_FACILITY_RATIO,
            )
