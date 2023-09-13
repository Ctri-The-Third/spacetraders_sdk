#! /bin/bash

python3 -m build
python3 -m pip uninstall straders_sdk -y
python3 -m pip install dist/straders-1.1.0-py3-none-any.whl --force-reinstall
