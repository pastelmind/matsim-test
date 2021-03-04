import csv
import pathlib

if __name__ == "__main__":
    base_dir = pathlib.Path(__file__, "../../scenario1").resolve()

    for child_dir in base_dir.iterdir():
        if not child_dir.is_dir():
            continue
        # Ignore output directories
        if child_dir.name.startswith("output"):
            continue

        print(child_dir.name + " " + "-" * 20)
        for file_path in child_dir.glob("*/scorestats.txt"):
            with file_path.open(newline="") as file:
                reader = csv.reader(file, dialect="excel-tab")
                *_, last_row = reader
                # print(file_path.parent.name + "\t" + last_row[3])
                print(last_row[3])
