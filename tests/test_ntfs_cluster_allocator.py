
import io
from fishy.ntfs.cluster_allocator import ClusterAllocator

class TestClusterAllocator(object):
    """ Tests the cluster allocator """
    def test_get_data(self, testfs_ntfs_stable1):
        """
        Tests if the correct data is returned
        """
        with open(testfs_ntfs_stable1[0], 'rb+') as fs,\
                open('utils/fs-files/another', 'rb') as to_hide:
            allocator = ClusterAllocator(fs)
            metadata = allocator.write(to_hide, 'long_file.txt')
            with io.BytesIO as mem:
                allocator.read(mem, metadata)
                assert  mem.read() == b'222\n'
