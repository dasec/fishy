# pylint: disable=missing-docstring, protected-access
import io
import os
import logging
import shutil
import subprocess
import tempfile
import unittest
from .cluster_allocator import ClusterAllocator


logging.basicConfig(level=logging.DEBUG)
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
UTILSDIR = os.path.join(THIS_DIR, os.pardir, os.pardir, 'utils')
IMAGEDIR = tempfile.mkdtemp()


class TestFATClusterAllocator(unittest.TestCase):
    image_paths = [
        os.path.join(IMAGEDIR, 'testfs-fat12-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat16-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat32-stable1.dd'),
        ]

    @classmethod
    def setUpClass(cls):
        # create test filesystems
        cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
              + " -d " + IMAGEDIR + " -t" + "fat" + " -u -s '-stable1'"
        subprocess.call(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, shell=True)

    @classmethod
    def tearDownClass(cls):
        # remove created filesystem images
        shutil.rmtree(IMAGEDIR)

    def test_write_single_cluster(self):
        for img_path in TestFATClusterAllocator.image_paths:
            with self.subTest(i=img_path):
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
                            self.assertEqual(result.start_cluster,
                                             expected_start_cluster)

    def test_write_directory(self):
        for img_path in TestFATClusterAllocator.image_paths:
            with self.subTest(i=img_path):
                with open(img_path, 'rb+') as img_stream:
                    # create Allocator object
                    fatfs = ClusterAllocator(img_stream)
                    with io.BytesIO() as mem:
                        teststring = "This is a simple write test."
                        mem.write(teststring.encode('utf-8'))
                        mem.seek(0)
                        with io.BufferedReader(mem) as reader:
                            with self.assertRaises(AssertionError):
                                fatfs.write(reader, 'onedirectory')

    def test_write_no_cluster(self):
        for img_path in TestFATClusterAllocator.image_paths:
            with self.subTest(i=img_path):
                with open(img_path, 'rb+') as img_stream:
                    # create Allocator object
                    fatfs = ClusterAllocator(img_stream)
                    with io.BytesIO() as mem:
                        teststring = "This is a simple write test."
                        mem.write(teststring.encode('utf-8'))
                        mem.seek(0)
                        with io.BufferedReader(mem) as reader:
                            with self.assertRaises(AssertionError):
                                fatfs.write(reader, 'areallylongfilenamethat' \
                                            + 'iwanttoreadcorrectly.txt')

    def test_read(self):
        for img_path in TestFATClusterAllocator.image_paths:
            with self.subTest(i=img_path):
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
                        self.assertEqual(result.decode('utf-8'), teststring)

    def test_clean(self):
        for img_path in TestFATClusterAllocator.image_paths:
            with self.subTest(i=img_path):
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
                    with self.assertRaises(Exception):
                        # try to read the content we wrote
                        with io.BytesIO() as mem:
                            fatfs.read(mem, write_res)
                    # read overwritten clusters
                    resulting = io.BytesIO()
                    for cluster_id in used_clusters:
                        fatfs.fatfs.cluster_to_stream(cluster_id, resulting)
                    resulting.seek(0)
                    # compare cluster content after write and after clear
                    self.assertNotEqual(resulting_bytes.read(),
                                        resulting.read())
