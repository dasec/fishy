#!/usr/bin/env python3

from setuptools import setup

setup(
    name='fishy',
    version='0.1',
    packages=['fishy', 'fishy.fat', 'fishy.fat.fat_filesystem'],
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
