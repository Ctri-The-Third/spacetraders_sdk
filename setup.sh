#! /bin/bash

python3 -m build
python3 -m pip uninstall straders -y
python3 -m pip install dist/straders-2.0.1-py3-none-any.whl --force-reinstall
