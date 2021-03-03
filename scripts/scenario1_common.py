"""Provides shared code for Scenario 1 (chessboard-like virtual map)."""
import datetime
import os
import pathlib
import random
from typing import Any, Dict, Optional, Tuple, Union

from .builders import ConfigBuilder, FacilitiesBuilder, NetworkBuilder, PlansBuilder
from .shared import Facility, random_time

# ---- Simulation parameters

# Range of departure times (end_time) for home -> workplace
DEPARTURE_TIME_RANGE_HOME = (datetime.time(7, 0, 0), datetime.time(8, 0, 0))
# Range of departure times (end_time) for workplace -> shop
DEPARTURE_TIME_RANGE_WORK = (datetime.time(17, 0, 0), datetime.time(18, 0, 0))
# Range of departure times (end_time) for shop -> home
DEPARTURE_TIME_RANGE_SHOP = (datetime.time(19, 0, 0), datetime.time(21, 0, 0))
# Controls the step size for randomly generated end_time values.
# This is either a datetime.timedelta object or None.
# Use None to use the smallest resolution possible (timedelta.resolution)
TIME_STEP = datetime.timedelta(minutes=10)


def generate(
    *,
    root_dir: Union[str, bytes, os.PathLike],
    random_seed: Any,
    rows: int,
    cols: int,
    block_size: float,
    agent_count: int,
    speed_limit: float,
    link_capacity: float,
    mix_work_and_shopping: bool,
    work_facility_ratio: Optional[float] = None,
    suffix: Optional[str] = None,
) -> None:
    """Generates a set of MATSim simulation files.

    Args:
        root_dir: Root directory to generate the XML files.
            If the directory does not exist, it will be created.
        random_seed: Seed value used to generate the scenario
        rows: Number of nodes in each column (== # of blocks + 1)
        cols: Number of nodes in each row (== # of blocks + 1)
        block_size: Width and height of each block
        agent_count: Number of agents
        speed_limit: Global speed limit in meters/second
        link_capacity: Global link capacity in vehicles/hour
        mix_work_and_shopping:
            If `True`, all work facilities are also shopping facilities and vice
            versa. If `False`, work facilities cannot be shopping facilities.
        work_facility_ratio:
            If `mix_work_and_shopping` is `False`, this parameter controls how
            many facilities in the inner region become work facilities.
            Acceptable values are between 0 (= no work facilities) and 1 (= all).
            If `mix_work_and_shopping` is `True`, this parameter has no effect.
        suffix: String to append to names of the generated files
    """
    random.seed(random_seed, version=2)
    if suffix is None:
        suffix = ""

    root_dir = pathlib.Path(root_dir).resolve()
    root_dir.mkdir(parents=True, exist_ok=True)

    network_file = f"network{suffix}.xml"
    facilities_file = f"facilities{suffix}.xml"
    plans_file = f"plans{suffix}.xml"

    # Generate the master config file
    config_builder = ConfigBuilder(
        network_file=network_file,
        facilities_file=facilities_file,
        plans_file=plans_file,
        output_dir=f"./output{suffix}",
        random_seed=random.randint(-(2 ** 63), 2 ** 63 - 1),
    )
    config_builder.write(str(root_dir / f"config{suffix}.xml"))

    # Generate the network (nodes and links)
    network_builder = NetworkBuilder()

    node_ids: Dict[Tuple[int, int], int] = {}
    for j in range(rows):
        for i in range(cols):
            node_ids[i, j] = network_builder.add_node(i * block_size, j * block_size)

    # Create vertical lanes
    for j in range(rows - 1):
        for i in range(cols):
            network_builder.add_2way_links(
                node_ids[i, j],
                node_ids[i, j + 1],
                length=block_size,
                freespeed=speed_limit,
                capacity=link_capacity,
            )
    # Create horizontal lanes
    for j in range(rows):
        for i in range(cols - 1):
            network_builder.add_2way_links(
                node_ids[i, j],
                node_ids[i + 1, j],
                length=block_size,
                freespeed=speed_limit,
                capacity=link_capacity,
            )

    network_builder.write(str(root_dir / network_file))

    # Generate facilities
    facilities = generate_facilities(
        rows=rows,
        cols=cols,
        block_size=block_size,
        facilities_file=str(root_dir / facilities_file),
        mix_work_and_shopping=mix_work_and_shopping,
        work_facility_ratio=work_facility_ratio,
    )

    # Generate agent plans
    plans_builder = PlansBuilder()

    fac_homes = [fac for fac in facilities.values() if "home" in fac.activity_types]
    fac_workplaces = [
        fac for fac in facilities.values() if "work" in fac.activity_types
    ]
    fac_shops = [fac for fac in facilities.values() if "shopping" in fac.activity_types]

    for _ in range(agent_count):
        # For each plan, randomly pick a (non-overlapping) home, workplace, and
        # shop
        home: Facility = random.choice(fac_homes)
        workplace: Facility = random.choice(
            [fac for fac in fac_workplaces if fac.id != home.id]
        )
        shop: Facility = random.choice(
            [fac for fac in fac_shops if fac.id != home.id and fac.id != workplace.id]
        )

        plans_builder.add_person(
            home=home,
            workplace=workplace,
            shop=shop,
            home_end_time=random_time(
                *DEPARTURE_TIME_RANGE_HOME,
                TIME_STEP,
            ),
            work_end_time=random_time(
                *DEPARTURE_TIME_RANGE_WORK,
                TIME_STEP,
            ),
            shopping_end_time=random_time(
                *DEPARTURE_TIME_RANGE_SHOP,
                TIME_STEP,
            ),
        )

    plans_builder.write(str(root_dir / plans_file))


def generate_facilities(
    *,
    rows: int,
    cols: int,
    block_size: float,
    facilities_file: str,
    mix_work_and_shopping: bool,
    work_facility_ratio: Optional[float] = None,
):
    """Generates facilities and saves them to a `facilities.xml` file.

    Args:
        rows: Number of nodes in each column (== # of blocks + 1)
        cols: Number of nodes in each row (== # of blocks + 1)
        block_size: Width and height of each block
        facilities_file: Path to save the `facilities.xml` to
        mix_work_and_shopping:
            If `True`, all work facilities are also shopping facilities and vice
            versa. If `False`, work facilities cannot be shopping facilities.
        work_facility_ratio:
            If `mix_work_and_shopping` is `False`, this parameter controls how
            many facilities in the inner region become work facilities.
            Acceptable values are between 0 (= no work facilities) and 1 (= all).
            If `mix_work_and_shopping` is `True`, this parameter has no effect.
    Returns:
        List of `Facility` objects that were written to disk
    """
    if not mix_work_and_shopping:
        inner_facility_count = max(0, rows - 1) * max(0, cols - 1)
        if work_facility_ratio is None:
            work_facility_ratio = 0.5
        work_facility_count = round(inner_facility_count * work_facility_ratio)
        inner_facility_pool = ["work"] * work_facility_count + ["shopping"] * (
            inner_facility_count - work_facility_count
        )
        random.shuffle(inner_facility_pool)

    facilities: Dict[int, Facility] = {}
    facilities_builder = FacilitiesBuilder()
    for j in range(-1, rows):
        for i in range(-1, cols):
            # Each facility is located at the center of the grid
            x = (i + 0.5) * block_size
            y = (j + 0.5) * block_size
            # Place homes in outer rings
            if i == -1 or i == cols - 1 or j == -1 or j == rows - 1:
                fac = facilities_builder.add_facility(x, y, ["home"])
            # Place work and shopping locations inside the inner blocks
            else:
                if mix_work_and_shopping:
                    fac = facilities_builder.add_facility(x, y, ["work", "shopping"])
                else:
                    facility_type = inner_facility_pool.pop()
                    fac = facilities_builder.add_facility(x, y, [facility_type])

            facilities[fac.id] = fac
    facilities_builder.write(facilities_file)
    return facilities
