#!/usr/bin/env python3

from setuptools import setup, find_packages
import unittest


def tests():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('.', pattern='test_*.py')
    return test_suite

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
        "pytsk3",
    ],
    test_suite='setup.tests',
)
