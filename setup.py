#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='fishy',
    version='0.1',
    packages=find_packages(),
    entry_points={
            'console_scripts': [
                'fishy = fishy.cli:main',
            ],
    },
    install_requires=[
        "argparse",
        "construct",
    ],
)
