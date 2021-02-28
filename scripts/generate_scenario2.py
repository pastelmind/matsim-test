"""Generates MATSim simulation scenarios from an existing `network.xml` file.

To execute this module, run:

    python -m scripts.generate_scenario2
"""
import datetime
import random
from os import path
from typing import (
    Collection,
    Dict,
    FrozenSet,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
)

from lxml import etree

from .builders import ConfigBuilder, FacilitiesBuilder, PlansBuilder
from .shared import ActivityType, Facility, random_time

# ---- Simulation parameters

# Random seed
# Note: This is also used to generate the seed for the scenario itself!
SEED = 847464097

# Number of agents (<person>s) to generate for the simulation.
# Note: The free version of Via only supports 500 maximum agents.
PERSON_COUNT = 5000

# Speed limit and link capacities are provided by the network.xml itself.
# # Global speed limit in (meters/second)
# SPEED_LIMIT = 50 * (1000 / 3600)  # Conversion from km/h to m/s
# # Global link capacity in (vehicles/hour)
# LINK_CAPACITY = 1000  # Arbitrary high value to remove congestion effects

# Range of departure times (end_time) for home -> workplace
DEPARTURE_TIME_RANGE_HOME = (datetime.time(7, 50, 0), datetime.time(8, 0, 0))
# Range of departure times (end_time) for workplace -> shop
DEPARTURE_TIME_RANGE_WORK = (datetime.time(17, 50, 0), datetime.time(18, 0, 0))
# Range of departure times (end_time) for shop -> home
DEPARTURE_TIME_RANGE_SHOP = (datetime.time(19, 50, 0), datetime.time(20, 0, 0))
# Controls the step size for randomly generated end_time values.
# This is either a datetime.timedelta object or None.
# Use None to use the smallest resolution possible (timedelta.resolution)
TIME_STEP = datetime.timedelta(seconds=30)


class NetworkNode(NamedTuple):
    """Represents a pre-generated `<node/>` tag in `network.xml`."""

    id: str
    x: str
    y: str


class NetworkLink(NamedTuple):
    """Represents a pre-generated `<link/>` tag in `network.xml`."""

    id: str
    from_: str
    to: str
    length: str
    freespeed: str
    capacity: str


def load_network(network_xml: bytes):
    """Loads a pre-built `network.xml` and extracts nodes and links.

    Args:
        network_xml: Contents of `network.xml`
    """
    root = etree.fromstring(network_xml)
    nodes = {
        node.attrib["id"]: NetworkNode(
            id=node.attrib["id"], x=node.attrib["x"], y=node.attrib["y"]
        )
        for node in root.findall(".//node")
    }
    links = {
        link.attrib["id"]: NetworkLink(
            id=link.attrib["id"],
            from_=link.attrib["from"],
            to=link.attrib["to"],
            length=link.attrib["length"],
            freespeed=link.attrib["freespeed"],
            capacity=link.attrib["capacity"],
        )
        for link in root.findall(".//link")
    }
    return nodes, links


def generate(
    *,
    facility_ratios: Mapping[Collection[ActivityType], float],
    suffix: Optional[str] = None,
) -> None:
    """Generates a set of MATSim simulation files.

    Args:
        facility_ratios:
            A mapping whose keys are collections of activity types, and values
            are the ratio of nodes to convert to facilities using said activity
            types.
            For example, the following `facility_ratio`...

                {
                    ("home", ): 0.5,
                    ("work", "shopping"): 0.3,
                }

            ...will convert 50% of the nodes to a "home" facility, and 30% of
            the nodes to a "work/shopping" facility, ignoring the remaining 20%.
        suffix: String to append to names of the generated files
    """
    random.seed(SEED, version=2)
    if suffix is None:
        suffix = ""

    scenario_dir = "scenario2"
    network_file = "network.xml"
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
    config_builder.write(path.join(scenario_dir, f"config{suffix}.xml"))

    # Load pre-generated network (nodes and links)
    with open(path.join(scenario_dir, network_file), mode="rb") as f:
        nodes, links = load_network(f.read())

    # Generate facilities
    facilities = generate_facilities(
        nodes=nodes.values(),
        facilities_file=path.join(scenario_dir, facilities_file),
        facility_ratios=facility_ratios,
    )

    # Generate agent plans
    plans_builder = PlansBuilder()

    fac_homes = [fac for fac in facilities.values() if "home" in fac.activity_types]
    fac_workplaces = [
        fac for fac in facilities.values() if "work" in fac.activity_types
    ]
    fac_shops = [fac for fac in facilities.values() if "shopping" in fac.activity_types]
    assert fac_homes
    assert fac_workplaces
    assert fac_shops

    for _ in range(PERSON_COUNT):
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

    plans_builder.write(path.join(scenario_dir, plans_file))


def generate_facilities(
    *,
    nodes: Sequence[NetworkNode],
    facilities_file: str,
    facility_ratios: Mapping[Collection[ActivityType], float],
) -> Dict[int, Facility]:
    """Generates facilities and saves them to a `facilities.xml` file.

    This function converts each node to a facility.

    Args:
        nodes: Pre-generated network nodes.
        facilities_file: Path to save the `facilities.xml` to
        facility_ratios:
            A mapping whose keys are collections of activity types, and values
            are the ratio of nodes to convert to facilities using said activity
            types.
    Returns:
        List of `Facility` objects that were written to disk
    """
    total_count = len(nodes)
    activity_pool: List[FrozenSet[ActivityType]] = []
    for activity_types, ratio in facility_ratios.items():
        if not isinstance(activity_types, Collection) or isinstance(
            activity_types, str
        ):
            raise TypeError(
                f"{activity_types!r} is an invalid key. facility_ratios must be keyed by a collection (e.g. tuple) of strings!"
            )
        amount = max(0, min(total_count, round(total_count * ratio)))
        activity_pool += [frozenset(activity_types)] * amount
    assert (
        len(activity_pool) <= total_count
    ), f"Sum of ratios must not exceed 1.0, got {sum(facility_ratios.values())}"

    random.shuffle(activity_pool)

    facilities: Dict[int, Facility] = {}
    facilities_builder = FacilitiesBuilder()
    for node, activity_types in zip(nodes, activity_pool):
        fac = facilities_builder.add_facility(node.x, node.y, activity_types)
        facilities[fac.id] = fac
    facilities_builder.write(facilities_file)
    return facilities


if __name__ == "__main__":
    generate(
        facility_ratios={
            ("home",): 0.4,
            ("work",): 0.5,
            ("shopping",): 0.1,
        },
        suffix=f"_segregated",
    )
    generate(
        facility_ratios={
            ("home",): 0.4,
            ("work", "shopping"): 0.6,
        },
        suffix=f"_mixed",
    )
