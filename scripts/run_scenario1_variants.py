"""Sequentially executes all variants of scenario 1
(the ones matching scenario1/*/config*.xml)

To execute this module, run:

    python -m scripts.run_scenario1_agents
"""
import pathlib
import subprocess

import colorama

if __name__ == "__main__":
    colorama.init()
    base_dir = pathlib.Path(__file__, "../../scenario1").resolve()

    for child_dir in base_dir.iterdir():
        if not child_dir.is_dir():
            continue
        # Ignore output directories
        if child_dir.name.startswith("output"):
            continue

        for config_file in child_dir.glob("config*.xml"):
            print(
                colorama.Fore.GREEN
                + colorama.Style.BRIGHT
                + f"Executing simulation for {config_file}"
                + colorama.Style.RESET_ALL
            )
            subprocess.run(
                f"java -cp ../../matsim-12.0.jar org.matsim.run.Controler {config_file}",
                cwd=child_dir,
            )
