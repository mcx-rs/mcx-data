import argparse
import os
import shutil
import subprocess
import yaml
from glob import glob
from os import path


with open("peripherals.yaml", "r") as f:
    all_peripherals_mapping = yaml.safe_load(f)


def get_device_mapped_peripherals(device):
    global all_peripherals_mapping
    mapped_peripherals = []
    for p in all_peripherals_mapping["peripherals"].items():
        op = None
        for m in p[1]:
            if m.startswith(f"{device}::"):
                op = m.removeprefix(f"{device}::")
                break
        if op is None:
            continue

        mapped_peripherals.append((op, p[0]))
    return mapped_peripherals


def copy_and_rename_peripherals():
    os.makedirs("temp/peripherals", exist_ok=True)

    for peripheral in all_peripherals_mapping["peripherals"].items():
        device, name = peripheral[1][0].split("::")
        shutil.copy(
            f"temp/{device}/{name}.yaml", f"temp/peripherals/{peripheral[0]}.yaml"
        )


def apply_transform(missing_ok=True):
    peripherals = [
        path.basename(f).removesuffix(".yaml") for f in glob("temp/peripherals/*.yaml")
    ]
    os.makedirs("peripherals", exist_ok=True)
    for p in peripherals:
        # if not path.exists(f"transforms/{p}.yaml") and not missing_ok:
        #     raise ValueError(f"Missing transform for {p}.")
        if not path.exists(f"transforms/{p}.yaml"):
            if not missing_ok:
                raise ValueError(f"Missing transform for {p}.")
            print("No transform for " + p)
            shutil.copy(f"temp/peripherals/{p}.yaml", f"peripherals/{p}.yaml")
            continue
        print("Transforming " + p)
        subprocess.run(
            [
                "chiptool",
                "transform",
                "-i",
                f"temp/peripherals/{p}.yaml",
                "-o",
                f"peripherals/{p}.yaml",
                "-t",
                f"transforms/{p}.yaml",
            ]
        )
    # create a file to indicate that the transforms have been applied
    open("peripherals/.applied", "w").close()


def check(device):
    subprocess.run(
        ["make", f"temp/{device}"], stdout=subprocess.PIPE
    ).check_returncode()
    files = glob(f"temp/{device}/*.yaml")
    all_peripherals = []
    for f in files:
        all_peripherals.append(path.basename(f).removesuffix(".yaml"))
    peripherals_mapping = get_device_mapped_peripherals(device)
    mapped_peripherals = [p[0] for p in peripherals_mapping]
    not_mapped_peripherals = list(set(all_peripherals).difference(mapped_peripherals))

    print(f"Device {device}")
    print("Mapped Peripherals:")
    for p in peripherals_mapping:
        print(f"  {p[0]} -> {p[1]}")
    print("Not Mapped Peripherals:")
    for p in not_mapped_peripherals:
        print(f"  {p}")


def transform(args):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="subcommand", help="sub-command help", required=True
    )
    # check
    parser_check = subparsers.add_parser(
        "check", help="check device peripherals states"
    )
    parser_check.add_argument("device")

    # transform
    parser_transform = subparsers.add_parser("transform")
    parser_transform.add_argument(
        "--skip-missing", help="skip missing transform", default=False
    )

    args = parser.parse_args()
    match args.subcommand:
        case "check":
            check(args.device)
