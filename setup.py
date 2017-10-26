#!/usr/bin/env python3

from setuptools import setup

setup(
    name='fishy',
    version='0.1',
    packages=['fishy', 'fishy.fat'],
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
