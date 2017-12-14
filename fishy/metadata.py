"""
Metadata is a simple class that holds and manages metadata.

Its purpose is to unify the dataformat and provide a consistent method for
reading and writing those metadata.

example of the resulting data structure that will be written to disk
(everything represented under the key 'metadata' comes from a
Sub-Metadata class and can vary, depending on the hiding technique)

    {
    "module": "fat-file-slack"
    "version": 2,
    "files": {
        "0": {
        "uid": "0",
        "filename": "test_file1.txt",
        "metadata": {
            "clusters": [
            [ 10, 512, 6 ]
            ]
        }
        },
        "1": {
        "uid": "1",
        "filename": "test_file2.txt",
        "metadata": {
            "clusters": [
            [ 3, 512, 6 ]
            ]
        }
        }
    },
    }

:Example:

first we create a Sub-Metadata class. It should be defined in each hiding
technique and specifies which data a hiding technique will store. In this
example we use the FileSlackMetadata class, because it is currently the only
one that exists.

>>> from fishy.fat.file_slack import FileSlackMetadata
>>> subm = FileSlackMetadata()
>>> subm.add_cluster(3, 512, 10)

now we create our metadata object and save the FileSlackMetadata object into it

>>> m = Metadata("fat-file-slack")
>>> m.add_file("super-secret-file.txt", subm)

we can get a single file entry out of it (if we now the uid)

>>> file_id = "0"
>>> m.get_file(file_id)
{'uid': '0', 'filename': 'super-secret-file.txt', 'metadata': {'clusters': [(3, 512, 10)]}}

or we can use the iterator to iterate over all file entries

>>> for entry in m.get_files():
...     print(entry)
{'uid': '0', 'filename': 'super-secret-file.txt', 'metadata': {'clusters': [(3, 512, 10)]}}

write metadata to a file

>>> mdf = open("/tmp/metadata.json", "w+")
>>> m.write(mdf)

read metadata file

>>> m = Metadata()
>>> mdf = open("/tmp/metadata.json", "r")
>>> m.read(mdf)

switch module context

>>> m.set_module("MyModule")
>>> m.get_module()
'MyModule'
"""

import json
import pprint
import typing as typ
from simplecrypt import encrypt, decrypt


class InformationMissingError(Exception):
    """
    This exception indicates, that some information in metadata
    are missing
    """
    pass


class Metadata:
    """
    holds metadata and gives modules a unified interface to
    store their information.
    """
    def __init__(self, module_identifier: str = "main", password = None):
        """
        :param module_identifier: string that uniquely identifies the
                                  current module. Default main.
        :password: password for encryption
        """
        self.metadata = {}
        self.password = password
        self.module = 'main'
        self.set("version", 2)
        self.set("files", {})
        self.set("module", None)
        self.set_module(module_identifier)

    def set_module(self, identifier: str) -> None:
        """
        sets the module identifier. use 'main' to switch back
        to main context.

        :param identifier: string that uniquely identifies the
                           current module
        """
        # create module context if it does not exist
        if identifier != "main":
            if self.metadata["module"] is None:
                self.metadata["module"] = identifier
            elif self.metadata["module"] != identifier:
                # avoid overwriting data from other modules
                # if they accidentially use this metadata
                raise Exception("This metadata was already "
                                + "initialized for module '%s'."
                                % self.metadata["module"])
        # save module identifier
        self.module = identifier

    def get_module(self) -> str:
        """
        get identifier string of the current active module

        :return: string that identifies the current active module
        """
        return self.module

    def set(self, key, value):
        """
        stores a key value pair. this method is only available in
        'main' context

        :param key: the key which itentifies the content
        :param value: value to store
        """
        if self.module == 'main':
            # if in main context, store it in root
            self.metadata[key] = value
        else:
            raise Exception("Only can store data in 'main' context")

    def get(self, key):
        """
        returns the value for a given key. this method is only available
        in 'main' context

        :param key: the key which itentifies the content
        :return: stored value
        """
        if self.module == "main":
            if key not in self.metadata:
                raise KeyError("Key '%s' not found in metadata" % key)
            return self.metadata[key]
        else:
            raise Exception("Only can read data in 'main' context")

    def generate_id(self) -> str:
        """
        generates a unique id, used as file identifier

        :return: string
        """
        return str(len(self.metadata["files"].keys()))

    def add_file(self, filename: str, submetadata) -> None:
        """
        store metadata defined in submodule for a file

        :param filename: sets the filename of the stored data.
                         if None, a name will be generated
        :param submetadata: Submetadata object, generated by hiding
                            technique
        """
        uid = self.generate_id()
        if filename is None:
            filename = uid
        self.metadata["files"][uid] = {
            'uid': uid,
            'filename': filename,
            'metadata': submetadata.__dict__
            }

    def get_file(self, file_id: int) -> typ.Dict:
        """
        get a file entry by its uid

        :param file_id: unique id of the file

        :return: dict of {uid, filename, submetadata}
        """
        if file_id not in self.metadata["files"]:
            raise KeyError("No file with id '%s' available")
        return self.metadata["files"][file_id]

    def get_files(self) -> typ.Dict:
        """
        iterator for all files in this metadata class

        :return: dict of {uid, filename, submetadata}
        """
        for key in self.metadata["files"].keys():
            yield self.metadata["files"][key]

    def read(self, instream: typ.BinaryIO) -> None:
        """
        reads json formatted content from stream.

        This will overwrite all content previously stored as metadata.
        The currently selected module will change to 'main'

        :param stream: stream to read from
        """
        if self.password is None:
            self.metadata = json.loads(instream.read().decode("utf8"))
        else:
            self.metadata = json.loads(decrypt(self.password, instream.read()).decode("utf8"))
        self.module = 'main'

    def write(self, outstream: typ.BinaryIO) -> None:
        """
        writes the current metadata into a stream
        """
        # check if some information are missing
        if self.metadata["module"] is None:
            raise InformationMissingError("Module identifier is missing")
        if "version" not in self.metadata:
            raise InformationMissingError("Metadata version is missing")

        # write metadata to stream
        if self.password is None:
            outstream.write(json.dumps(self.metadata).encode("utf8"))
        else:
            outstream.write(encrypt(self.password, json.dumps(self.metadata)))
        outstream.flush()

    def info(self) -> None:
        """
        prints info about stored metadata
        """
        ppp = pprint.PrettyPrinter(indent=4)
        # metadata main attributes
        print("Version:", self.metadata["version"])
        print("Module Identifier:", self.metadata["module"])
        print("Stored Files:")
        for uid in self.metadata["files"].keys():
            file_meta = self.metadata["files"][uid]
            print("  File_ID:", file_meta["uid"])
            print("  Filename:", file_meta["filename"])
            print("  Associated File Metadata:")
            print("    ", end="")
            ppp.pprint(file_meta["metadata"])
