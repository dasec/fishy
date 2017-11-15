# pylint: disable=missing-docstring, protected-access
"""
These tests run against fishy.fat.cluster_allocator which implements the
additional cluster allocation hiding technique for FAT filesystems
"""
import io
import pytest
from fishy.fat.cluster_allocator import ClusterAllocator


class TestWrite(object):
    """ Test write method """
    def test_write_single_cluster(self, testfs_fat_stable1):
        """ Test if writing to a single additional cluster works """
        for img_path in testfs_fat_stable1:
            with open(img_path, 'rb+') as img_stream:
                # create Allocator object
                fatfs = ClusterAllocator(img_stream)
                expected_start_cluster = fatfs.fatfs.get_free_cluster()
                # setup raw stream and write testmessage
                with io.BytesIO() as mem:
                    teststring = "This is a simple write test."
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    # write testmessage to disk
                    with io.BufferedReader(mem) as reader:
                        result = fatfs.write(reader, 'another')
                        assert result.start_cluster \
                                == expected_start_cluster

    def test_write_directory(self, testfs_fat_stable1):
        """ Test if writing to a directory fails """
        for img_path in testfs_fat_stable1:
            with open(img_path, 'rb+') as img_stream:
                # create Allocator object
                fatfs = ClusterAllocator(img_stream)
                with io.BytesIO() as mem:
                    teststring = "This is a simple write test."
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        with pytest.raises(AssertionError):
                            fatfs.write(reader, 'onedirectory')

    def test_write_no_cluster(self, testfs_fat_stable1):
        """ Test if writing to a file without allocated clusters fails """
        for img_path in testfs_fat_stable1:
            with open(img_path, 'rb+') as img_stream:
                # create Allocator object
                fatfs = ClusterAllocator(img_stream)
                with io.BytesIO() as mem:
                    teststring = "This is a simple write test."
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        with pytest.raises(AssertionError):
                            fatfs.write(reader, 'areallylongfilenamethat' \
                                        + 'iwanttoreadcorrectly.txt')

class TestRead(object):
    """ Test read method """
    def test_read(self, testfs_fat_stable1):
        """ Test if reading from a single additional cluster works """
        for img_path in testfs_fat_stable1:
            with open(img_path, 'rb+') as img_stream:
                # create Allocator object
                fatfs = ClusterAllocator(img_stream)
                teststring = "This is a simple write test."
                # write content that we want to read
                with io.BytesIO() as mem:
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        write_res = fatfs.write(reader, 'long_file.txt')
                # read content we wrote and compare result with
                # our initial test message
                with io.BytesIO() as mem:
                    fatfs.read(mem, write_res)
                    mem.seek(0)
                    result = mem.read()
                    assert result.decode('utf-8') == teststring

    def test_read_multi_cluster(self, testfs_fat_stable1):
        """ Test if reading from multiple additional clusters works """
        for img_path in testfs_fat_stable1:
            with open(img_path, 'rb+') as img_stream:
                # create Allocator object
                fatfs = ClusterAllocator(img_stream)
                teststring = "This is a simple write test."*80
                # write content that we want to read
                with io.BytesIO() as mem:
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        write_res = fatfs.write(reader, 'another')
                # read clusters
                result = io.BytesIO()
                fatfs.read(result, write_res)
                result.seek(0)
                # compare cluster content
                assert result.read() == teststring.encode('utf-8')

class TestClean(object):
    def test_clean(self, testfs_fat_stable1):
        """ Test if cleaning additional clusters works """
        for img_path in testfs_fat_stable1:
            with open(img_path, 'rb+') as img_stream:
                # create Allocator object
                fatfs = ClusterAllocator(img_stream)
                teststring = "This is a simple write test."
                # write content that we want to read
                with io.BytesIO() as mem:
                    mem.write(teststring.encode('utf-8'))
                    mem.seek(0)
                    with io.BufferedReader(mem) as reader:
                        write_res = fatfs.write(reader, 'long_file.txt')
                # save written bytes
                resulting_bytes = io.BytesIO()
                fatfs.fatfs.file_to_stream(write_res.get_start_cluster(),
                                           resulting_bytes)
                resulting_bytes.seek(0)
                # save used clusters
                used_clusters = fatfs.fatfs.follow_cluster(write_res.start_cluster)
                fatfs.clear(write_res)
                with pytest.raises(Exception):
                    # try to read the content we wrote
                    with io.BytesIO() as mem:
                        fatfs.read(mem, write_res)
                # read overwritten clusters
                resulting = io.BytesIO()
                for cluster_id in used_clusters:
                    fatfs.fatfs.cluster_to_stream(cluster_id, resulting)
                resulting.seek(0)
                # compare cluster content after write and after clear
                assert resulting_bytes.read() != resulting.read()
