import os
import re
import shutil
import subprocess
from glob import glob
from os import path
from typing import Dict, List

import yaml


class PeripheralMapping(object):
    def __init__(self, f: str, mapping: Dict[str, List[str]]) -> None:
        self.f = f
        self.mapping = mapping

    def contain_device(self, device: str) -> List[str] | None:
        for r, opnames in self.mapping.items():
            if len(re.findall(r, device)) != 0:
                return opnames
        return None

    @classmethod
    def from_dict(cls, dict) -> "PeripheralMapping":
        return cls(dict["from"], dict["mapping"])

    def __str__(self) -> str:
        return f"from: {self.f}, mapping: {self.mapping}"


class PeripheralMappings(object):
    def __init__(self, mappings: Dict[str, PeripheralMapping]) -> None:
        self.mappings = mappings

    def get_mapped_peripheral_name(self, device: str, block: str) -> str | None:
        for pname, mapping in self.mappings.items():
            opnames = mapping.contain_device(device)
            if opnames == None:
                continue
            for opname in opnames:
                if opname == block:
                    return pname
        return None

    @classmethod
    def parse(cls, path="./peripherals.yaml") -> "PeripheralMappings":
        with open(path, "r") as f:
            d = yaml.safe_load(f)
        for k, v in d.items():
            d[k] = PeripheralMapping.from_dict(v)
        return cls(d)

    def __str__(self) -> str:
        s = ""
        for k, m in self.mappings.items():
            s += f"{k}: {m}\n"
        s.removesuffix("\n")
        return s


def get_device_mapped_peripherals(device: str) -> List:
    _peripherals = PeripheralMappings.parse()
    mapped_peripherals = []
    for pname, mapping in _peripherals.items():
        for r, opnames in mapping.items():
            if r == "from":
                continue
            match = re.findall(f"^{r}$", device)
            if len(match) != 1:
                continue
            l = [(pname, x) for x in opnames]
            mapped_peripherals.extend(l)

    return mapped_peripherals


def copy_and_rename_peripherals():
    _peripherals = PeripheralMappings.parse()
    os.makedirs("temp/peripherals", exist_ok=True)
    for pname, mapping in _peripherals.mappings.items():
        device = mapping.f
        op = mapping.contain_device(device)
        if op is None:
            continue
        op = op[0]
        shutil.copy(f"temp/{device}/{op}.yaml", f"temp/peripherals/{pname}.yaml")


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
