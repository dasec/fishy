
import io
import pytest
from fishy.ntfs.cluster_allocator import ClusterAllocator


class TestClusterAllocator(object):
    """ Tests the cluster allocator """
    # @pytest.mark.xfail
    def test_get_data(self, testfs_ntfs_stable1):
        """
        Tests if the correct data is returned
        """
        with open(testfs_ntfs_stable1[0], 'rb+') as fs,\
                open('utils/fs-files/another', 'rb') as to_hide1:
            allocator = ClusterAllocator(fs)
            metadata = allocator.write(to_hide1, 'long_file.txt')
            with io.BytesIO() as mem:
                allocator.read(mem, metadata)
                mem.seek(0)
                assert  mem.read() == b'222\n'

            to_hide2 = io.BytesIO(b'2'*7000)
            metadata = allocator.write(to_hide2, 'long_file.txt')
            with io.BytesIO() as mem:
                allocator.read(mem, metadata)
                mem.seek(0)
                assert  mem.read() == b'2'*7000

            allocator.clear(metadata)
            with io.BytesIO() as mem:
                allocator.read(mem, metadata)
                mem.seek(0)
                assert  mem.read() == b'0'*7000

