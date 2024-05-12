import os
import shutil
import subprocess
from glob import glob
from os import path
from typing import Dict, List

import yaml

with open("peripherals.yaml", "r") as f:
    _peripherals: Dict[str, Dict[str, List[str]]] = yaml.safe_load(f)


def get_device_mapped_peripherals(device: str) -> List:
    mapped_peripherals = []
    for p in _peripherals:
        if device in _peripherals[p]:
            # l = peripherals[p][device]
            mapped_peripherals.extend([(p, x) for x in _peripherals[p][device]])
    return mapped_peripherals


def copy_and_rename_peripherals():
    os.makedirs("temp/peripherals", exist_ok=True)
    for p in _peripherals:
        device = list(_peripherals[p].keys())
        device.sort()
        device = device[0]
        name = _peripherals[p][device][0]
        shutil.copy(f"temp/{device}/{name}.yaml", f"temp/peripherals/{p}.yaml")


def apply_transform(missing_ok: bool = True):
    periph_names = [
        path.basename(f).removesuffix(".yaml") for f in glob("temp/peripherals/*.yaml")
    ]
    os.makedirs("peripherals", exist_ok=True)
    for name in periph_names:
        if not path.exists(f"transforms/{name}.yaml"):
            if not missing_ok:
                raise ValueError(f"Missing transform for {name}.")
            print("No transform for " + name)
            shutil.copy(f"temp/peripherals/{name}.yaml", f"peripherals/{name}.yaml")
            continue
        print("Transforming " + name)
        subprocess.run(
            [
                "chiptool",
                "transform",
                "-i",
                f"temp/peripherals/{name}.yaml",
                "-o",
                f"peripherals/{name}.yaml",
                "-t",
                f"transforms/{name}.yaml",
            ],
            stdout=subprocess.PIPE,
        ).check_returncode()
