import importlib.metadata as md
import os
import platform
from enum import Enum, auto
from platform import python_version
from typing import List


def show_package_version(
    packages: list[str] = None,
    sep: str = " | ",
    include_demo_packages: bool = True,
) -> None:
    """
    Display the versions of the specified packages.

    Parameters:
        packages (list[str], optional): A list of package names. Defaults to ["pandas","numpy","duckdb","pandas-plots", "connection_helper"].
        sep (str, optional): The separator to use when joining the package names and versions. Defaults to " | ".
        include_demo_packages: If True, inlude all demo packages

    Returns:
        None
    """
    # ! avoid empty list in signature, it will NOT be empty in runtime
    if packages is None:
        packages = []

    if not isinstance(packages, List):
        print(f"❌ A list of str must be provided")
        return
    demo = [
        "pandas",
        "numpy",
        "duckdb",
        "pandas-plots",
        "connection-helper",
    ]
    items = []
    items.append(f"🐍 {python_version()}")
    if include_demo_packages:
        packages.extend(demo)

    for item in packages:
        try:
            version = md.version(item)
            items.append(f"📦 {item}: {version}")
        except md.PackageNotFoundError:
            items.append(f"❌ {item}: Not found")
    out = sep.join(items).strip()
    print(out)
    return

class OperatingSystem(Enum):
    WINDOWS = auto()
    LINUX = auto()
    MAC = auto()

def get_os(is_os: OperatingSystem = None, verbose: bool = False) -> bool | str:
    """
    A function that checks the operating system and returns a boolean value based on the operating system to check.

    Parameters:
        is_os (OperatingSystem): The operating system to check against. Defaults to None.
        Values are
            - OperatingSystem.WINDOWS
            - OperatingSystem.LINUX
            - OperatingSystem.MAC

    Returns:
        bool: True if the desired operating system matches the current operating system, False otherwise.
        str: Returns the current operating system (platform.system()) if is_os is None.
    """
    if verbose:
        print(
            f"💻 os: {os.name} | 🎯 system: {platform.system()} | 💽 release: {platform.release()}"
        )

    if is_os is None:
        return platform.system()

    if is_os == OperatingSystem.WINDOWS and platform.system() == "Windows":
        return True
    elif is_os == OperatingSystem.LINUX and platform.system() == "Linux":
        return True
    elif is_os == OperatingSystem.MAC and platform.system() == "Darwin":
        return True
    else:
        return False