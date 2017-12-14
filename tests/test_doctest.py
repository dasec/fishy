"""
This test module runs doctests against selected modules
"""

import doctest
import unittest
import xmlrunner
import fishy.metadata

def load_tests(loader, tests, ignore):
    # add doctests for metadata module
    tests.addTests(doctest.DocTestSuite(fishy.metadata))
    return tests

if __name__ == '__main__':
    with open('doctests.xml', 'wb') as output:
            unittest.main(
                testRunner=xmlrunner.XMLTestRunner(output=output),
                failfast=False, buffer=False, catchbreak=False)
