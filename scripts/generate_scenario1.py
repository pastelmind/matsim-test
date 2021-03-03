"""Generates MATSim simulation scenarios from scratch, creating a
chessboard-like network.

To execute this module, run:

    python -m scripts.generate_scenario1
"""
from .scenario1_common import generate

# ---- Simulation parameters

# Random seed
# Note: This is also used to generate the seed for the scenario itself!
SEED = 4759245
# Number of nodes (vertices) in horizontal direction
X_NODES = 10
# Number of nodes (vertices) in vertical direction
Y_NODES = 10
# List of width/height values of each grid in meters
GRID_SIZES = [250, 500, 1000]
# Number of agents (<person>s) to generate for the simulation.
# Note: The free version of Via only supports 500 maximum agents.
PERSON_COUNT = 500
# Global speed limit in (meters/second)
SPEED_LIMIT = 50 * (1000 / 3600)  # Conversion from km/h to m/s
# Global link capacity in (vehicles/hour)
LINK_CAPACITY = 1000  # Arbitrary high value to remove congestion effects


if __name__ == "__main__":
    for grid_size in GRID_SIZES:
        generate(
            root_dir="scenario1",
            random_seed=SEED,
            rows=Y_NODES,
            cols=X_NODES,
            block_size=grid_size,
            agent_count=PERSON_COUNT,
            speed_limit=SPEED_LIMIT,
            link_capacity=LINK_CAPACITY,
            suffix=f"_segregated_{grid_size}",
            mix_work_and_shopping=False,
            work_facility_ratio=0.5,
        )
        generate(
            root_dir="scenario1",
            random_seed=SEED,
            rows=Y_NODES,
            cols=X_NODES,
            block_size=grid_size,
            agent_count=PERSON_COUNT,
            speed_limit=SPEED_LIMIT,
            link_capacity=LINK_CAPACITY,
            suffix=f"_mixed_{grid_size}",
            mix_work_and_shopping=True,
        )
