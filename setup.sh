#! /bin/bash

python3 -m build
python3 -m pip uninstall straders -y
python3 -m pip install dist/straders-1.2.2-py3-none-any.whl --force-reinstall
