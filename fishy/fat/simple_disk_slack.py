"""
example:
>>> f = open('/dev/sdb1', 'rb+')
>>> fs = SimpleDiskSlack(f)

"""


from fat_wrapper import FAT
from io import BytesIO, BufferedReader

class SimpleDiskSlack:
    def __init__(self, stream):
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
        calculates the slack space for a given DirEntry
        :param entry: DirEntry, directory entry of the file
        :return: tuple of (occupation, free_slack), whereas occupation
                 is the occupied size of the last cluster by the file.
                 And free_slack is the size of the slack space
        """
        cluster_size = self.fs.pre.sector_size * \
                       self.fs.pre.sectors_per_cluster
        occupied_of_last_cluster = entry.fileSize % cluster_size
        free_slack = cluster_size - occupied_of_last_cluster
        return (occupied_of_last_cluster, free_slack)

    def write(self, instream, filepath):
        """
        writes from instream into slackspace of filename
        :param instream: stream to read from
        :param filepath: path to file, which slackspace will be used
        """
        # get directory entry for file
        entry = self._find_file(filepath)
        if entry.start_cluster < 2:
            raise IOError("File '%s' has no slackspace" % filepath)
        # calculate slack space
        occupied_of_last_cluster, free_slack = self.calculate_slack_space(entry)
        if free_slack == 0:
            raise IOError("No slack space available for file '%s'" \
                           % filepath)
        # read what to write
        bufferv = instream.read()
        if len(bufferv) > free_slack:
            raise IOError("Not enough slack space available to write input")
        last_cluster = self.fs.follow_cluster(entry.start_cluster).pop()
        last_cluster_start = self.fs.get_cluster_start(last_cluster)
        self.stream.seek(last_cluster_start + occupied_of_last_cluster)
        self.stream.write(bufferv)

    def read(self, outstream, filepath):
        """
        writes from instream into slackspace of filename
        :param instream: stream to write into
        :param filepath: path to file, which slackspace will be used
        """
        # get directory entry for file
        entry = self._find_file(filepath)
        if entry.start_cluster < 2:
            raise IOError("File '%s' has no slackspace" % filepath)
        # calculate slack space
        occupied_of_last_cluster, free_slack = self.calculate_slack_space(entry)
        # read slack space
        last_cluster = self.fs.follow_cluster(entry.start_cluster).pop()
        last_cluster_start = self.fs.get_cluster_start(last_cluster)
        self.stream.seek(last_cluster_start + occupied_of_last_cluster)

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


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Read and write into slackspace of a file')
    parser.add_argument('-d', '--device', dest='dev', required=True, help='Path to filesystem')
    parser.add_argument('-f', '--file', dest='file', required=True, help='absolute path to file on filesystem')
    parser.add_argument('-r', '--read', dest='read', action='store_true', help='read from slackspace')
    parser.add_argument('-w', '--write', dest='write', action='store_true', help='write to slackspace')
    parser.add_argument('-c', '--clear', dest='clear', action='store_true', help='clear slackspace')
    args = parser.parse_args()

    # just for supid testing while we dont have a nicer cli option
    f = open(args.dev, 'rb+')
    filename = args.file
    fs = SimpleDiskSlack(f)
    if args.write:
        fs.write(sys.stdin.buffer, filename)
    if args.read:
        fs.read(sys.stdout.buffer, filename)
    if args.clear:
        fs.clear(filename)
