# depreciated, using python-build with a pyproject.toml instead

import setuptools
from setuptools import find_packages

setuptools.setup(
    package_dir={
        "straders": "straders_sdk",  # Map "straders" package to "straders_sdk" directory
        "straders.pathfinder": "straders_sdk/pathfinder",  # Map "
        "straders.pg_pieces": "straders_sdk/pg_pieces",  # Map "straders.pg_pieces" package to "straders_sdk/pg_pieces" directory
        "straders.clients": "straders_sdk/clients",  # Map "straders.clients" package to "straders_sdk/clients" directory
        "straders.models": "straders_sdk/models",  # Map "straders.models" package to "straders_sdk/models" directory
        "straders.responses": "straders_sdk/responses",  # Map "straders.responses" package to "straders_sdk/responses" directory
    },
    packages=[
        "straders_sdk",
        "straders_sdk.pg_pieces",
        "straders_sdk.pathfinder",
        "straders_sdk.clients",
        "straders_sdk.models",
        "straders_sdk.responses",
    ],
)
