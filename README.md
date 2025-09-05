## Bootstrap the socket-bp-patch environment

Create a new project from this template with copier:
```
copier copy git@gitlab.polytech.umontpellier.fr:enseignants-informatique/python_package_template.git ./destination_folder
```
Once created:

```bash
# Create virtual environment using venv
python -m venv .venv
# Activate virtual environment (you should then see (.venv) or something similar before your prompt)
source .venv/bin/activate
# Install the current project as a package in editable mode
pip install -e .
# Get info about the package
pip show socket-bp-patch
# Install quality tools
pip install -r requirements-dev.txt
# You will need a git repo to use pre-commit
git init
```

The files ruff.toml, tox.ini, mkdocs.yml, and .pre-commit-config.yaml are either empty or incomplete.


## Try tox
```bash
# Run everything
tox
# Run a single tox environment (here the tests for python 3.12)
tox -e py312
```

## Cleanup

```bash
# Leave the virtual environment
deactivate
```
