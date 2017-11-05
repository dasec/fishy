from .ntfsSlack import NtfsSlack
from .ntfsSlack import FileSlackMetadata

class NTFSFileSlack:
    def __init__(self, stream):
        """
        :param stream: filedescriptor of a FAT filesystem
        """
        self.stream = stream
        self.slackTool = NtfsSlack(stream)
    

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
        m = self.slackTool.write(instream, filepaths)
        return m

    def read(self, outstream, metadata):
        """
        writes slackspace of files into outstream
        :param outstream: stream to write into
        :param metadata: FileSlackMetadata object
        """
        self.slackTool.read(outstream, metadata)

    def clear(self, metadata):
        """
        clears the slackspace of a files
        :param metadata: FileSlackMetadata object
        """
        self.slackTool.clear(metadata)
