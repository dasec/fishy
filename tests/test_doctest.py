"""
This test module runs doctests against selected modules
"""

import doctest
import unittest
import fishy.metadata

def load_tests(loader, tests, ignore):
    # add doctests for metadata module
    tests.addTests(doctest.DocTestSuite(fishy.metadata))
    return tests
