"""
FileSlack offers methods to read, write and
clear the slackspace of a given file in FAT filesystems

Implementation is mainly realized as described by [1], but
extended in terms of respecting RAM slack padding of Windows
and Linux FAT implementations [2].

[1]: Shu-fen-2009
[2]: Berghel2008

usage example:
>>> f = open('/dev/sdb1', 'rb+')
>>> fs = FileSlack(f)
>>> filenames = [ 'afile.txt' ]

to write something from stdin into slack:
>>> metadata = fs.write(sys.stdin.buffer, filenames)

to read something from slack to stdout:
>>> fs.read(sys.stdout.buffer, metadata)

to wipe slackspace of a file:
>>> fs.clear(metadata)
"""

import logging
import typing as typ
from .fat_filesystem.fat_wrapper import create_fat
from .fat_filesystem.dir_entry import DirEntry

LOGGER = logging.getLogger("fat-file-slack")


class FileSlackMetadata:
    """
    holds file slack information, which are generated during write.
    """
    def __init__(self, d: dict = None):
        """
        :param d: dict, dictionary representation of a FileSlackMetadata
                  object
        """
        if d is None:
            self.clusters = []
        else:
            self.clusters = d["clusters"]

    def add_cluster(self, cluster_id: int, offset: int, length: int) -> None:
        """
        adds a cluster to the list of clusters
        :param cluster_id: int, id of the cluster
        :param offset: int, offset, where the fileslack begins
        :param length: int, length of the data, which was written
                       to fileslack
        """
        self.clusters.append((cluster_id, offset, length))

    def get_clusters(self) \
            -> typ.Generator[typ.Tuple[int, int, int], None, None]:
        """
        iterator for clusters
        :returns: iterator, that returns cluster_id, offset, length
        """
        for cluster in self.clusters:
            yield cluster[0], cluster[1], cluster[2]


class FileSlack:
    """
    Provides methods to manipulate the slack space of files in FAT filesystems.
    """
    def __init__(self, stream: typ.BinaryIO):
        """
        :param stream: filedescriptor of a FAT filesystem
        """
        self.fatfs = create_fat(stream)
        self.stream = stream

    def _file_walk(self, directory: DirEntry) -> \
            typ.Generator[DirEntry, None, None]:
        """
        get file entries of directories recusively
        :param directory: entry point; needs to be a directory
        :returns: generator that traverses file entries of directories
                  recursively
        """
        assert directory.is_dir(), "supplied entry is not a directory"
        if directory is not None:
            start_dir = directory.get_start_cluster()
        for entry in self.fatfs.get_dir_entries(start_dir):
            if entry.is_dot_entry():
                # skip dot entries
                continue
            if entry.is_dir():
                # recurse into subdirectory
                yield from self._file_walk(entry)
            else:
                # exclude all file entries that dont allocate any cluster
                if entry.get_start_cluster() > 1:
                    yield entry

    def calculate_slack_space(self, entry: DirEntry) -> typ.Tuple[int, int]:
        """
        calculates the slack space for a given DirEntry
        :param entry: DirEntry, directory entry of the file
        :return: tuple of (occupation, free_slack), whereas occupation
                 is the occupied size of the last cluster by the file.
                 And free_slack is the size of the slack space
        """
        # calculate how many bytes belong to a cluster
        cluster_size = self.fatfs.pre.sector_size * \
            self.fatfs.pre.sectors_per_cluster
        # calculate of many bytes the original file
        # occupies in this cluster
        occupied_by_file = entry.get_filesize() % cluster_size
        # calculate ram slack (how many free bytes remain for)
        # this sector. As at least under linux (no other os tested)
        # padds ram slack with zeros, we should not write into this
        # space as this might seem suspicious
        ram_slack = (self.fatfs.pre.sector_size
                     - (occupied_by_file % self.fatfs.pre.sector_size)) \
                     % self.fatfs.pre.sector_size
        # calculate remaining free slack size in this cluster
        free_slack = cluster_size - occupied_by_file - ram_slack
        return (occupied_by_file, ram_slack, free_slack)

    def _get_writable_file(self, filepaths: typ.List[str]) \
            -> typ.Generator[DirEntry, None, None]:
        """
        get the next writable file out of a filepaths list, while also
        traversing into subdirectories, if some appear in that list
        :param filepaths: list of strings, that link to files or directories
                          on the fat filesystem
        """
        # Turn filepaths list into a set, to avoid duplicate files that would
        # lead to overwriting content that was already witten
        filepaths = list(set(filepaths))
        for filepath in filepaths:
            entry = self.fatfs.find_file(filepath)
            if entry.is_dir():
                # if the user supplied path is a directory, we will use all
                # files from it as possible files where we can exploit file
                # slack. Attention: This might be a place, where files can
                # be used twice, when the user specifies:
                # ['adir/file.txt', 'adir'] we would write twice to
                # 'adir/file.txt'
                # TODO: Find a suitable fix for problem described above
                yield from self._file_walk(entry)
            else:
                yield entry
        yield None

    def write(self, instream: typ.BinaryIO, filepaths: typ.List[str]) \
            -> FileSlackMetadata:
        """
        writes from instream into slackspace of filename
        :param instream: stream to read from
        :param filepaths: list of strings, paths to files, which slackspace
                          will be used
        :return: FileSlackMetadata
        """
        metadata = FileSlackMetadata()
        next_file = self._get_writable_file(filepaths)
        while instream.peek():
            entry = next(next_file)
            if entry is None:
                # dont do anything, if we dont have files anymore
                break
            occupied, ram_slack, free_slack = self.calculate_slack_space(entry)
            if free_slack == 0 or entry.get_start_cluster() < 2:
                # if current entry has no slack space, continue with next entry
                continue
            written_bytes, cluster_id = self._write_to_slack(instream, entry)
            LOGGER.info("%d bytes written into cluster %d",
                        written_bytes, cluster_id)
            metadata.add_cluster(cluster_id, occupied + ram_slack,
                                 written_bytes)

        if instream.peek():
            self.clear(metadata)
            raise IOError("No slack space left, to write data. But there are"
                          + " still %d Bytes in stream" % len(instream.peek()))
        return metadata

    def _write_to_slack(self, instream: typ.BinaryIO, entry: DirEntry) \
            -> typ.Tuple[int, int]:
        """
        writes from instream into slackspace of filename
        :param instream: stream to read from
        :param entry: DirectoryEntry, of the file which slackspace will be used
        :return: tuple of (number of bytes written, cluster_id written to)
        """
        occupied, ram_slack, free_slack = self.calculate_slack_space(entry)
        # read what to write. ensure that we only read the amount of data,
        # that fits into slack
        bufferv = instream.read(free_slack)
        LOGGER.info("%d bytes read from instream", len(bufferv))
        # find position where we can start writing data
        last_cluster = self.fatfs.follow_cluster(entry.get_start_cluster()).pop()
        last_cluster_start = self.fatfs.get_cluster_start(last_cluster)
        self.stream.seek(last_cluster_start + occupied + ram_slack)
        # write bytes into stream
        bytes_written = self.stream.write(bufferv)
        return bytes_written, last_cluster

    def read(self, outstream: typ.BinaryIO, metadata: FileSlackMetadata) \
            -> None:
        """
        writes slackspace of files into outstream
        :param outstream: stream to write into
        :param metadata: FileSlackMetadata object
        """
        for cluster_id, offset, length in metadata.get_clusters():
            cluster_start = self.fatfs.get_cluster_start(cluster_id)
            self.stream.seek(cluster_start + offset)
            bufferv = self.stream.read(length)
            outstream.write(bufferv)

    def clear(self, metadata: FileSlackMetadata) -> None:
        """
        clears the slackspace of a files
        :param metadata: FileSlackMetadata object
        """
        for cluster_id, offset, length in metadata.get_clusters():
            cluster_start = self.fatfs.get_cluster_start(cluster_id)
            self.stream.seek(cluster_start + offset)
            self.stream.write(length * b'\x00')
