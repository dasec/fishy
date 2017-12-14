"""
interface for ntfs slack implementation
"""

from .ntfsSlack import NtfsSlack

class NTFSFileSlack:
    """calls ntfsSlack methods  """
    def __init__(self, stream):
        """
        :param stream: filedescriptor of a FAT filesystem
        """
        self.stream = stream
        self.slack_tool = NtfsSlack(stream)    

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
        meta = self.slack_tool.write(instream, filepaths)
        return meta

    def read(self, outstream, metadata):
        """
        writes slackspace of files into outstream
        :param outstream: stream to write into
        :param metadata: FileSlackMetadata object
        """
        self.slack_tool.read(outstream, metadata)

    def clear(self, metadata):
        """
        clears the slackspace of a files
        :param metadata: FileSlackMetadata object
        """
        self.slack_tool.clear(metadata)

    def info(self, filepaths):
        """
        prints info about available file slack of files
        """
        self.slack_tool.filepath = filepaths
        self.slack_tool.info = True
        self.slack_tool.filesize_left = float('inf')
        self.slack_tool.fill_slack_list()
        print("\nTotal slack:%s"%self.slack_tool.total_slacksize)
        return self.slack_tool.total_slacksize
    