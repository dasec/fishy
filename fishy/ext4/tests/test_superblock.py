from unittest import TestCase
from ..superblock import Superblock
import pprint

pp = pprint.PrettyPrinter(indent=4)


class TestSuperblock(TestCase):

    image = "ext4_example_wc.img"

    def test_parse_superblock(self):
        sb = Superblock(self.image)

        pp.pprint(sb.data)
        keys = sb.structure.keys()

        hasAllKeys = True
        for key in keys:
            if not key in sb.data:
                hasAllKeys = False
                break

        self.assertTrue(hasAllKeys)
