# pylint: disable=missing-docstring
"""
These tests run against fishy.cli while simulating calls via command line.
"""
import io
import json
import os
import sys
import tempfile
import pytest
from fishy import cli


class CaptureStdout(list):
    """
    capture stdout output of a function into a list

    usage:
        >>> with CaptureStdout() as output:
        >>>     cli.main()
        >>> output[0]
        b'the cli output'
    """
    def __enter__(self):
        self._stdout = sys.stdout  # pylint: disable=attribute-defined-outside-init
        self._bytestream = io.BytesIO()  # pylint: disable=attribute-defined-outside-init
        sys.stdout = self._iow = io.BufferedWriter(self._bytestream)  # pylint: disable=attribute-defined-outside-init
        sys.stdout.buffer = self._iow2 = io.BufferedWriter(self._bytestream)  # pylint: disable=attribute-defined-outside-init
        return self

    def __exit__(self, *args):
        self._iow.seek(0)
        self._iow2.seek(0)
        self.extend(self._bytestream)
        del self._iow    # free up some memory
        del self._iow2    # free up some memory
        del self._bytestream
        sys.stdout = self._stdout


class TestCliFileSlack(object):
    """ test fileslack subcommand """

    def test_write_fileslack_from_file(self, testfs_fat_stable1):
        """
        Test if writing from a file into the slackspace of a given
        destination works.
        """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        testfilename = os.path.basename(testfilepath)
        metadata_file = tempfile.NamedTemporaryFile().name
        expected = json.dumps(json.loads('{"version": 2, "files": {"0": ' \
                   + '{"uid": "0", "filename": ' \
                   + '"' + testfilename + '", "metadata": {"clusters": ' \
                   + '[[3, 512, 18]]}}}, "module": "fat-file-slack"}'))
        # create test file which we will hide
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_fat_stable1:
            # write metadata
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # compare outputted metadata
            with open(metadata_file) as metaf:
                metafcontent = metaf.read()
            assert metafcontent == expected
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_write_fileslack_from_stdin(self, testfs_fat_stable1):
        """
        Test if writing fro stdin into the slackspace of a given destination
        works.
        """
        teststring = "Small test for CLI"
        metadata_file = tempfile.NamedTemporaryFile().name
        expected = json.dumps(json.loads('{"version": 2, "files": {"0": ' \
                   + '{"uid": "0", "filename": ' \
                   + '"0", "metadata": {"clusters": ' \
                   + '[[3, 512, 18]]}}}, "module": "fat-file-slack"}'))
        for img_path in testfs_fat_stable1:
            # write metadata
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file]
            sys.argv = args
            with io.BufferedRandom(io.BytesIO()) as patch_buffer:
                # save real stdin before monkey pathing it
                real_stdin = sys.stdin
                sys.stdin = patch_buffer
                sys.stdin.buffer = patch_buffer
                sys.stdin.write(teststring.encode('utf-8'))
                patch_buffer.seek(0)
                cli.main()
                # restore real stdin
                sys.stdin = real_stdin
            # compare outputted metadata
            with open(metadata_file) as metaf:
                metafcontent = metaf.read()
            assert metafcontent == expected
        # remove testfiles
        os.remove(metadata_file)

    def test_read_fileslack_stdout(self, testfs_fat_stable1):
        """ Test if reading from fileslack into stdout works """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_fat_stable1:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content
            args = ["fishy", "-d", img_path, "fileslack", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            # compare stdout output with string we gave as input
            with CaptureStdout() as output:
                cli.main()
            assert output[0].decode('utf-8') == teststring
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_read_fileslack_outfile(self, testfs_fat_stable1):
        """ Test if reading from slackspace into a given output file works """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        outfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_fat_stable1:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content into file
            args = ["fishy", "-d", img_path, "fileslack", "-o", outfilepath,
                    "-m", metadata_file]
            sys.argv = args
            cli.main()
            with open(outfilepath, 'r') as outfile:
                result = outfile.read()
                assert result == teststring
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)
        os.remove(outfilepath)

    def test_clear_fileslack(self, testfs_fat_stable1):
        """ Test if clearing the slackspace works """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_fat_stable1:
            # write something we want to clear
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # clear the written information
            args = ["fishy", "-d", img_path, "fileslack", "-c", "-m",
                    metadata_file]
            sys.argv = args
            cli.main()
            args = ["fishy", "-d", img_path, "fileslack", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            with CaptureStdout() as output:
                cli.main()
            expected = len(teststring.encode('utf-8')) * b'\x00'
            assert output[0] == expected
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)


class TestCliClusterAllocation(object):
    """ test addcluster subcommand """

    def test_write_from_file(self, testfs_fat_stable1):
        """ Test if writing from from a file into additional clusters works """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_fat_stable1:
            # write metadata
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # check if there is a file in metadata
            with open(metadata_file) as metaf:
                metafcontent = json.loads(metaf.read())
            filecount = len(metafcontent['files'])
            assert filecount == 1
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_write_from_stdin(self, testfs_fat_stable1):
        """ Test if writing from from stdin into additional clusters works """
        teststring = "Small test for CLI"
        metadata_file = tempfile.NamedTemporaryFile().name
        for img_path in testfs_fat_stable1:
            # write metadata
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file]
            sys.argv = args
            with io.BufferedRandom(io.BytesIO()) as patch_buffer:
                # save real stdin before monkey pathing it
                real_stdin = sys.stdin
                sys.stdin = patch_buffer
                sys.stdin.buffer = patch_buffer
                sys.stdin.write(teststring.encode('utf-8'))
                patch_buffer.seek(0)
                cli.main()
                # restore real stdin
                sys.stdin = real_stdin
            # check if there is a file in metadata
            with open(metadata_file) as metaf:
                metafcontent = json.loads(metaf.read())
            filecount = len(metafcontent['files'])
            assert filecount == 1
        # remove testfiles
        os.remove(metadata_file)

    def test_read_stdout(self, testfs_fat_stable1):
        """ Test if reading from additional clusters to stdout works """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_fat_stable1:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content
            args = ["fishy", "-d", img_path, "addcluster", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            # compare stdout output with string we gave as input
            with CaptureStdout() as output:
                cli.main()
            assert output[0].decode('utf-8') == teststring
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_read_outfile(self, testfs_fat_stable1):
        """
        Test if reading from additional clusters to a given output file
        works.
        """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        outfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_fat_stable1:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content into file
            args = ["fishy", "-d", img_path, "addcluster", "-o", outfilepath,
                    "-m", metadata_file]
            sys.argv = args
            cli.main()
            with open(outfilepath, 'r') as outfile:
                result = outfile.read()
                assert result == teststring
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)
        os.remove(outfilepath)

    def test_clear(self, testfs_fat_stable1):
        """ Test if clearing additional clusters works """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_fat_stable1:
            # write something we want to clear
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # clear the written information
            args = ["fishy", "-d", img_path, "addcluster", "-c", "-m",
                    metadata_file]
            sys.argv = args
            cli.main()
            args = ["fishy", "-d", img_path, "addcluster", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            with pytest.raises(Exception):
                cli.main()
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

class TestCliMftSlack(object):
    """ test mftslack subcommand """

    def test_write_mft_slack(self, testfs_ntfs_stable1):
        """
        Test if writing from file to mft slack works with offset.
        """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        testfilename = os.path.basename(testfilepath)
        metadata_file = tempfile.NamedTemporaryFile().name
        expected = json.dumps(json.loads('{"version": 2, "files": {"0": ' \
                   + '{"uid": "0", "filename": ' \
                   + '"' + testfilename + '", "metadata": {"addrs": ' \
                   + '[[41584, 18, 0]]}}}, "module": "ntfs-mft-slack"}'))
        # create test file which we will hide
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_ntfs_stable1:
            # write metadata
            args = ["fishy", "-d", img_path, "mftslack", "-w", "-s", "80",
                    "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # compare outputted metadata
            with open(metadata_file) as metaf:
                metafcontent = metaf.read()
            assert metafcontent == expected
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_write_fileslack_from_stdin(self, testfs_ntfs_stable1):
        """
        Test if writing fro stdin into the mft slackspace works.
        """
        teststring = "Small test for CLI"
        metadata_file = tempfile.NamedTemporaryFile().name
        expected = json.dumps(json.loads('{"version": 2, "files": {"0": ' \
                   + '{"uid": "0", "filename": ' \
                   + '"0", "metadata": {"addrs": ' \
                   + '[[16792, 18, 0]]}}}, "module": "ntfs-mft-slack"}'))
        for img_path in testfs_ntfs_stable1:
            # write metadata
            args = ["fishy", "-d", img_path, "mftslack", "-w",
                    "-m", metadata_file]
            sys.argv = args
            with io.BufferedRandom(io.BytesIO()) as patch_buffer:
                # save real stdin before monkey pathing it
                real_stdin = sys.stdin
                sys.stdin = patch_buffer
                sys.stdin.buffer = patch_buffer
                sys.stdin.write(teststring.encode('utf-8'))
                patch_buffer.seek(0)
                cli.main()
                # restore real stdin
                sys.stdin = real_stdin
            # compare outputted metadata
            with open(metadata_file) as metaf:
                metafcontent = metaf.read()
            assert metafcontent == expected
        # remove testfiles
        os.remove(metadata_file)

    def test_read_fileslack_stdout(self, testfs_ntfs_stable1):
        """ Test if reading from mftslack into stdout works """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_ntfs_stable1:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "mftslack", "-w",
                    "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content
            args = ["fishy", "-d", img_path, "mftslack", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            # compare stdout output with string we gave as input
            with CaptureStdout() as output:
                cli.main()
            assert output[0].decode('utf-8') == teststring
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_read_fileslack_outfile(self, testfs_ntfs_stable1):
        """ Test if reading from slackspace into a given output file works """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        outfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_ntfs_stable1:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "mftslack", "-w",
                    "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content into file
            args = ["fishy", "-d", img_path, "mftslack", "-o", outfilepath,
                    "-m", metadata_file]
            sys.argv = args
            cli.main()
            with open(outfilepath, 'r') as outfile:
                result = outfile.read()
                assert result == teststring
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)
        os.remove(outfilepath)

    def test_clear_fileslack(self, testfs_ntfs_stable1):
        """ Test if clearing the slackspace works """
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in testfs_ntfs_stable1:
            # write something we want to clear
            args = ["fishy", "-d", img_path, "mftslack", "-w",
                    "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # clear the written information
            args = ["fishy", "-d", img_path, "mftslack", "-c", "-m",
                    metadata_file]
            sys.argv = args
            cli.main()
            args = ["fishy", "-d", img_path, "mftslack", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            with CaptureStdout() as output:
                cli.main()
            expected = len(teststring.encode('utf-8')) * b'\x00'
            assert output[0] == expected
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

