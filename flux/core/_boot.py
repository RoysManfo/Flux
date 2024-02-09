import os
import platform
import subprocess
from typing import List, Optional

from flux.utils import environment


class _Warning:
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description


class _Report:
    def __init__(self) -> None:
        self.can_start = True
        self.warnings: List[_Warning] = []


report = _Report()
root_dir = os.path.realpath(os.path.join(
    os.path.realpath(__file__), "..", "..", ".."))
verbose = False


def boot(dev_mode: bool = False) -> _Report:
    """
    Handles environment and minimum dependencies, and makes 
    `:param dev_mode`: if set to True, outputs on stdout all output
    `:returns` : A _Report object that determines if the application can start without problems
    """
    global verbose
    verbose = dev_mode

    if environment.is_in_venv():
        # TODO: check requirements, and install them if necessary
        report.can_start = handle_min_requirements()
        return report

    return report


def install_requirements(dep: List[str]) -> Optional[subprocess.CompletedProcess]:
    try:
        interp = environment.get_interpreter_command()
        pip = environment.get_pip_command()
        command = [interp, "-m", pip, "install"]
        if not verbose:
            dep_list = '\n  -  '.join(dep)
            print(f"installing: {dep_list}")

        subprocess.run(command + ["--upgrade", "--user", "pip"],
                       capture_output=(not verbose), text=True, check=True)
        return subprocess.run(command + dep, capture_output=(not verbose), text=True, check=True)
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

                return requirements

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

    import importlib
    to_install = []

    for req in minim:
        try:
            m = importlib.import_module(req)
            del m
        except ModuleNotFoundError:
            to_install.append(req)

    if to_install:
        p = install_requirements(to_install)
        return p is not None and p.returncode == 0

    return True
