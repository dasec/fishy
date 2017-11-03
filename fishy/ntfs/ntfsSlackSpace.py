from .ntfsSlack import NtfsSlack
from .ntfsSlack import FileSlackMetadata

class NTFSFileSlack:
    def __init__(self, stream):
        """
        :param stream: filedescriptor of a FAT filesystem
        """
        self.stream = stream
        self.slackTool = NtfsSlack(stream)
    
    

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
        if filepaths is None:
            filepaths = ["/"]
        # find directory entry for given filepath
        filepath = filepaths.pop()
        m = self.slackTool.write(instream, filepath)
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
