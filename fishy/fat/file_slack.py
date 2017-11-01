"""
SimpleFileSlack offers methods to read, write and
clear the slackspace of a given file in FAT filesystems

example:
>>> f = open('/dev/sdb1', 'rb+')
>>> fs = SimpleFileSlack(f)
>>> filename = 'path/to/file/on/fs'

to write something from stdin into slack:
>>> fs.write(sys.stdin.buffer, filename)

to read something from slack to stdout:
>>> fs.read(sys.stdout.buffer, filename)

to wipe slackspace of a file:
>>> fs.clear(filename)
"""


from .fat_filesystem.fat_wrapper import FAT
from io import BytesIO, BufferedReader

class FileSlackMetadata:
    def __init__(self, d=None):
        """
        :param d: dict, dictionary representation of a FileSlackMetadata
                  object
        """
        if d is None:
            self.clusters = []
        else:
            self.clusters = d["clusters"]

    def add_cluster(self, cluster_id, offset, length):
        """
        adds a cluster to the list of clusters
        :param cluster_id: int, id of the cluster
        :param offset: int, offset, where the fileslack begins
        :param length: int, length of the data, which was written
                       to fileslack
        """
        self.clusters.append((cluster_id, offset, length))

    def get_clusters(self):
        """
        iterator for clusters
        :returns: iterator, that returns cluster_id, offset, length
        """
        for c in self.clusters:
            yield c[0], c[1], c[2]


class FileSlack:
    def __init__(self, stream):
        """
        :param stream: filedescriptor of a FAT filesystem
        """
        self.fs = FAT(stream)
        self.stream = stream

    def _find_file(self, filepath):
        """
        returns the directory entry for a given filepath
        :param filepath: string, filepath to the file
        :return: DirEntry of the requested file
        """
        # build up filepath as directory and
        # reverse it so, that we can simple
        # pop all filepath parts from it
        path = filepath.split('/')
        path = list(reversed(path))
        # read root directory and append all entries
        # as a tuple of (entry, lfn), that have a non
        # empty lfn
        # TODO: This excludes filesystems without long
        #       filename extension. Should we support
        #       them?
        current_directory = []
        for entry, lfn in self.fs.get_root_dir_entries():
            if lfn != "":
                current_directory.append( (entry, lfn) )

        while len(path) > 0:
            fpart = path.pop()

            # scan current directory for filename
            filename_found = False
            for entry, lfn in current_directory:
                if lfn == fpart:
                    filename_found = True
                    break
            if not filename_found:
                raise Exception("File or directory '%s' not found" % fpart)

            # if it is a subdirectory, enter it
            if entry.attributes.subDirectory:
                current_directory = []
                for entry, lfn in self.fs.get_dir_entries(entry.start_cluster):
                    if lfn != "":
                        current_directory.append( (entry, lfn) )
        return entry

    def _file_walk(self, directory=None):
        """
        iterator, returns file entries of directories, while
        traversing the filesystem recursively.
        :param directory: entry point, if not given, root
                          directory will be used
        """
        raise NotImplementedError()

    def calculate_slack_space(self, entry):
        """
        calculates the slack space for a given DirEntry
        :param entry: DirEntry, directory entry of the file
        :return: tuple of (occupation, free_slack), whereas occupation
                 is the occupied size of the last cluster by the file.
                 And free_slack is the size of the slack space
        """
        # calculate how many bytes belong to a cluster
        cluster_size = self.fs.pre.sector_size * \
            self.fs.pre.sectors_per_cluster
        # calculate of many bytes the original file
        # occupies in this cluster
        occupied_by_file = entry.fileSize % cluster_size
        # calculate ram slack (how many free bytes remain for)
        # this sector. As at least under linux (no other os tested)
        # padds ram slack with zeros, we should not write into this
        # space as this might seem suspicious
        ram_slack = (self.fs.pre.sector_size - \
                    (occupied_by_file % self.fs.pre.sector_size)) % \
                    self.fs.pre.sector_size
        # calculate remaining free slack size in this cluster
        free_slack = cluster_size - occupied_by_file - ram_slack
        return (occupied_by_file + ram_slack, free_slack)

    def write(self, instream, filepaths):
        """
        writes from instream into slackspace of filename
        :param instream: stream to read from
        :param filepaths: list of strings, paths to files, which slackspace
                          will be used
        :return: FileSlackMetadata
        """
        file_length = 0
        m = FileSlackMetadata()
        while instream.peek():
            if len(filepaths) == 0:
                # dont do anything, if we dont have any files
                break
            # find directory entry for given filepath
            filepath = filepaths.pop()
            entry = self._find_file(filepath)
            if entry.attributes.subDirectory:
                # if current entry is a directory, traverse it
                raise Exception("traversing directories not implemented")
                self._file_walk(entry)
            occupied, free_slack = self.calculate_slack_space(entry)
            if free_slack == 0 or entry.start_cluster < 2:
                # if current entry has no slack space, continue with next
                # entry
                continue
            written_bytes, cluster_id = self._write_to_slack(instream, entry)
            m.add_cluster(cluster_id, occupied, written_bytes)

        if instream.peek():
            raise IOError("No slack space left, to write data")
        return m

    def _write_to_slack(self, instream, entry):
        """
        writes from instream into slackspace of filename
        :param instream: stream to read from
        :param entry: DirectoryEntry, of the file which slackspace will be used
        :return: tuple of (number of bytes written, cluster_id written to)
        """
        occupied, free_slack = self.calculate_slack_space(entry)
        # read what to write. ensure that we only read the amount of data,
        # that fits into slack
        bufferv = instream.read(free_slack)
        # find position where we can start writing data
        last_cluster = self.fs.follow_cluster(entry.start_cluster).pop()
        last_cluster_start = self.fs.get_cluster_start(last_cluster)
        self.stream.seek(last_cluster_start + occupied)
        # write bytes into stream
        bytes_written = self.stream.write(bufferv)
        return bytes_written, last_cluster

    def read(self, outstream, metadata):
        """
        writes slackspace of files into outstream
        :param outstream: stream to write into
        :param metadata: FileSlackMetadata object
        """
        for cluster_id, offset, length in metadata.get_clusters():
            cluster_start = self.fs.get_cluster_start(cluster_id)
            self.stream.seek(cluster_start + offset)
            bufferv = self.stream.read(length)
            outstream.write(bufferv)

    def clear(self, metadata):
        """
        clears the slackspace of a files
        :param metadata: FileSlackMetadata object
        """
        for cluster_id, offset, length in metadata.get_clusters():
            cluster_start = self.fs.get_cluster_start(cluster_id)
            self.stream.seek(cluster_start + offset)
            self.stream.write(length * b'\x00')
