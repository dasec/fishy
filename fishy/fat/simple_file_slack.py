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


from .fat_filesystem.fat_wrapper import create_fat
from io import BytesIO, BufferedReader


class SimpleFileSlack:
    def __init__(self, stream):
        """
        :param stream: filedescriptor of a FAT filesystem
        """
        self.fs = create_fat(stream)
        self.stream = stream

    def _find_file(self, filepath):
        """
        returns the directory entry for a given filepath
        :param filepath: string, filepath to the file
        :return: DIR_ENTRY of the requested file
        """
        # build up filepath as directory and
        # reverse it so, that we can simple
        # pop all filepath parts from it
        path = filepath.split('/')
        path = list(reversed(path))
        # read root directory and append all entries
        # as a tuple of (entry, lfn), that have a non
        # empty lfn
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

    def calculate_slack_space(self, entry):
        """
        calculates the slack space for a given DIR_ENTRY
        :param entry: DIR_ENTRY, directory entry of the file
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
        ram_slack = (self.fs.pre.sector_size -
                    (occupied_by_file % self.fs.pre.sector_size)) % \
                    self.fs.pre.sector_size
        # calculate remaining free slack size in this cluster
        free_slack = cluster_size - occupied_by_file - ram_slack
        return (occupied_by_file + ram_slack, free_slack)

    def write(self, instream, filepath):
        """
        writes from instream into slackspace of filename
        :param instream: stream to read from
        :param filepath: path to file, which slackspace will be used
        :raises: IOError
        """
        # get directory entry for file
        entry = self._find_file(filepath)
        if entry.start_cluster < 2 or entry.fileSize == 0:
            raise IOError("File '%s' has no slackspace" % filepath)
        # calculate slack space
        occupied, free_slack = self.calculate_slack_space(entry)
        if free_slack == 0:
            raise IOError("No slack space available for file '%s'"
                          % filepath)
        # read what to write. ensure that we only read the amount of data,
        # that fits into slack
        bufferv = instream.read(free_slack)
        # check if there is still data in instream. if that is the case
        # the user wants to write more data than we can store.
        if instream.peek():
            raise IOError("Not enough slack space available to write input")
        # find position where we can start writing data
        last_cluster = self.fs.follow_cluster(entry.start_cluster).pop()
        last_cluster_start = self.fs.get_cluster_start(last_cluster)
        self.stream.seek(last_cluster_start + occupied)
        # write bytes into stream
        self.stream.write(bufferv)

    def read(self, outstream, filepath):
        """
        writes from instream into slackspace of filename
        :param instream: stream to write into
        :param filepath: path to file, which slackspace will be used
        :raises: IOError
        """
        # get directory entry for file
        entry = self._find_file(filepath)
        if entry.start_cluster < 2:
            raise IOError("File '%s' has no slackspace" % filepath)
        # calculate slack space
        occupied, free_slack = self.calculate_slack_space(entry)
        # read slack space
        last_cluster = self.fs.follow_cluster(entry.start_cluster).pop()
        last_cluster_start = self.fs.get_cluster_start(last_cluster)
        self.stream.seek(last_cluster_start + occupied)

        bufferv = self.stream.read(free_slack)
        outstream.write(bufferv)

    def clear(self, filepath):
        """
        clears the slackspace of a given file
        :param filepath: string, path to file
        """
        # calculate slack space size
        entry = self._find_file(filepath)
        occupied, slack_size = self.calculate_slack_space(entry)
        # write zeros into stream
        with BytesIO() as mem:
            data = slack_size * b'\x00'
            mem.write(data)
            mem.seek(0)
            with BufferedReader(mem) as reader:
                self.write(reader, filepath)
