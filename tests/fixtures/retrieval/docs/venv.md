# Virtual environments and packages

## Why use a virtual environment
A virtual environment is a private folder with its own Python and its own installed packages. Each project gets one, so a package version you need here cannot break another project. Create one with `python -m venv .venv`.

## Activating on each system
On Windows PowerShell run `.venv\Scripts\Activate.ps1`. On macOS and Linux run `source .venv/bin/activate`. When it works, the prompt starts with `(.venv)`. If PowerShell says that running scripts is disabled on this system, change the execution policy for your user, or call the Python inside `.venv\Scripts` directly.

## Installing packages
With the environment active, run `pip install requests`. Use `python -m pip` to be sure you use the pip that belongs to the active Python. If you see `ModuleNotFoundError: No module named 'requests'`, the package is missing from the Python that runs your script, often because the environment is not active or pip installed it somewhere else.

## Recording what you installed
Run `pip freeze > requirements.txt` to list exact versions, and `pip install -r requirements.txt` to rebuild the environment on another machine. Do not commit the `.venv` folder itself; commit only the requirements file.
