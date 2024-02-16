"""
### Flux Boot (Flux's boot sequence)

These procedures allow flux to run in an isolated environment
and are necessary to handle missing requirements and ensure that Flux can start without issues
"""

import os
import platform
import subprocess
from typing import List, Optional
import logging

from flux.utils import environment

class _Warning:
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    def __str__(self) -> str:

        if not self.description:
            return f"[!] {self.name}"
        return f"[!] {self.name}: {self.description}"

class _Report:
    def __init__(self) -> None:
        self.can_start = True
        self.warnings: List[_Warning] = []


report = _Report()
root_dir = os.path.realpath(os.path.join(
    os.path.realpath(__file__), "..", "..", ".."))

def boot(dev_mode: bool = False) -> _Report:
    """
    Handles environment and minimum dependencies, and makes 
    `:param dev_mode`: if set to True, outputs on stdout all output
    `:returns` : A _Report object that determines if the application can start without problems
    """

    if dev_mode:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    logging.debug("checking virtual environment")
    if environment.is_in_venv():
        logging.debug(f"found virtual environment: {environment.get_venv_name()} ({environment.get_venv_location()})")
        if not environment.is_in_flux_env():

            action = input(f"Environment {environment.get_venv_name()} does not contain a .fluxenv file, create one (y/n):  ").lower()
            if action == 'y':
                fluxenv = os.path.join(environment.get_venv_location(), ".fluxenv")
                logging.debug(f"creating file {fluxenv}")
                with open(fluxenv,'w') as f:
                    f.write("# This file was automaticaly created by Flux\n\n")

                logging.debug(f"fluxenv initialization completed")
            else:
                report.can_start = False
                report.warnings.append(_Warning("Not in flux environment", f"the .fluxenv file is missing in {environment.get_venv_location()}"))
                return report
        
        # TODO: check requirements, and install them if necessary
        logging.debug(f"checking requirements in {environment.get_venv_location()}")
        report.can_start = handle_min_requirements()
        logging.debug(f"fboot completed...    system setup")
        return report


    report.can_start = False
    report.warnings.append(_Warning("Unable to start", f"Flux is unable to complete the setup procedures"))
    return report


def install_requirements(dep: List[str]) -> Optional[subprocess.CompletedProcess]:
    try:
        interp = environment.get_interpreter_path()
        pip = environment.get_pip_command()
        command = [interp, "-m", pip, "install"]

        logging.info(f"upgrading pip")
        subprocess.run(command + ["--upgrade", pip], check=True)
        logging.info(f"installing: {'\n  -  '.join(dep)}")
        return subprocess.run(command + dep, capture_output=(logging.root.level > logging.DEBUG), text=True, check=True)
    except subprocess.CalledProcessError as e:
        report.warnings.append(_Warning(e.__class__.__name__, e.stderr))


def get_minimum_requirements() -> Optional[List[str]]:
    """
    `:returns` : A list containing all minimum dependencies needed or None in case of error (es. FileNotFound, IOError, ...)   
    """
    req = os.path.join(root_dir, "requirements.txt")

    if os.path.exists(req):
        try:
            with open(req) as file:
                requirements = file.read().splitlines()

                OS_NAME = platform.system().lower()

                if OS_NAME.startswith("win"):
                    requirements += get_windows_requirements()
                elif OS_NAME in ["linux", "darwin"]:
                    requirements += get_linux_requirements()

                # ensure no duplicates are present (NOTE: this isn't perfect, but works fine)
                return list(set(requirements)) 

        except:
            # error reading file
            return None
    # file does not exist
    return None


def get_windows_requirements() -> List[str]:
    """
    Requirements specific to windows
    """

    dep = [
        "mutagen==1.47.0",
        "pydub==0.25.1",
        "PyPDF2==3.0.1",
        "python-magic-bin==0.4.14",
    ]

    return dep


def get_linux_requirements() -> List[str]:
    """
    Requirements specific to linux
    """

    dep = [
        "mutagen==1.47.0",
        "pydub==0.25.1",
        "PyPDF2==3.0.1",
    ]

    return dep


def handle_min_requirements() -> bool:
    """
    `:returns` : True if all the minimum requirements are/have been installed, False otherwhise 
    """
    minim = get_minimum_requirements()

    if not minim:
        return False

    to_install = []
    wrong_version: list[tuple[str, str]] = []

    try:
        result = subprocess.run([environment.get_interpreter_path(), "-m", environment.get_pip_command(), "freeze"], capture_output=True, text=True)
        packages = result.stdout.split('\n')
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        packages = None
        report.warnings.append(_Warning(e.__class__.__name__, e.__str__()))
        return False

    package_names = []
    if packages:
        package_names = [i.split('==')[0] for i in packages if i != '']
    else:
        report.warnings.append(_Warning("Unable to check package version", ""))

    for req in minim:
        req_parts = req.split("==")

        if (req_parts[0] not in package_names):
            to_install.append(req)
        else:
            # requirement installed, check version
            if packages:
                for package in packages:
                    # check the name and version
                    if package.startswith(req_parts[0]) and package.split('==')[-1] != req_parts[-1]:
                        # wrong version
                        wrong_version.append((req, package))
                        report.warnings.append(
                            _Warning(
                                "Wrong version found",
                                f"Package {req_parts[0]} found with version {package.split("==")[-1]} instead of {req_parts[-1]}"
                                )
                            )

    if to_install:
        p = install_requirements(to_install)
        return p is not None and p.returncode == 0

    return True