#!/usr/bin/env python3

from setuptools import setup, find_packages, Distribution


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
        "construct < 2.9",
        "pytsk3",
        "simple-crypt",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    extras_require={
        'build_sphinx': ['sphinx', 'sphinx-argparse'],
    },
)
