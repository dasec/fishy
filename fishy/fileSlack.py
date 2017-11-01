from .filesystem_detector import get_filesystem_type
from .fat.file_slack import FileSlack as FATFileSlack
from .fat.file_slack import FileSlackMetadata as FATFileSlackMetadata


class FileSlack:
    """
    This class wrapps the filesystem specific file slack implementations

    usage examples:

    >>> f = open('/dev/sdb1', 'rb+')
    >>> fs = FileSlack(f)
    >>> m = Metadata("FileSlack")
    >>> filenames = [ 'path/to/file/on/fs' ]

    to write something from stdin into slack:
    >>> fs.write(sys.stdin.buffer, m, filenames)

    to read something from slack to stdout:
    >>> fs.read(sys.stdout.buffer, m)

    to wipe slackspace via metadata file:
    >>> fs.clear_with_metadata(m)

    to wipe slackspace via providing filepaths
    >>> fs.clear_with_filepaths(filenames)
    """
    def __init__(self, fs_stream):
        """
        :param fs_stream: Stream of filesystem
        :param metadata: Metadata object
        """
        self.metadata = None
        self.fs_type = get_filesystem_type(fs_stream)
        if self.fs_type == 'FAT':
            self.fs = FATFileSlack(fs_stream)
        else:
            raise NotImplementedError()

    def write(self, instream, filepaths, filename=None):
        """
        writes data from instream into slackspace of filepaths. Metadata of
        those files will be stored in Metadata object

        :param instream: stream to read data from
        :param filepaths: list of strings, paths to files, which slackspace
                          will be used to store data
        :param filename: name that will be used, when file gets written into a
                         directory (while reading fileslack). if none, a random
                         name will be generated
        :raises: IOError
        """
        # self.metadata = Metadata()
        if self.fs_type == 'FAT':
            # self.metadata.set_module("fat-file-slack")
            slack_metadata = self.fs.write(instream, filepaths)
            # self.metadata.add_file(filename, slack_metadata)
        else:
            raise NotImplementedError()

    def read(self, outstream, file_id):
        """
        writes hidden data from slackspace into stream. The examined slack
        space information is taken from metadata.

        :param outstream: stream to write hidden data into
        :param file_id: id of the file, that will be written into stream.
        :raises: IOError
        """
        if self.fs_type == 'FAT':
            self.metadata.set_module("fat-file-slack")
        else:
            raise NotImplementedError()
        file_metadata = self.metadata.get_file_metadata(file_id)
        self.fs.read(outstream, file_metadata)

    def clear_with_metadata(self, metadata):
        """
        clears the slackspace of files. Information of them is stored in
        metadata.
        :param metadata: Metadata, object where metadata is stored in
        :raises: IOError
        """
        raise NotImplementedError()

    def clear_with_filepaths(self, filepaths):
        """
        clears the slackspace of files.
        :param filepaths: list of strings, filepaths to files, which slackspace
                          will be cleared
        :raises: IOError
        """
        raise NotImplementedError()
