# depreciated, using python-build with a pyproject.toml instead

import setuptools
from setuptools import find_packages

setuptools.setup(
    packages=["straders_sdk"],
    package_dir={
        "straders": "straders_sdk",  # Map "straders" package to "straders_sdk" directory
        "straders.pg_pieces": "straders_sdk/pg_pieces",  # Map "straders.pg_pieces" package to "straders_sdk/pg_pieces" directory
    },
)
