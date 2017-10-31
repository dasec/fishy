"""
Metadata is a simple class that holds and manages metadata.

Its purpose is to unify the dataformat and provide a consistent method for
reading and writing those metadata. Therefor it provides a simple key-value
store.

example:

>>> m = Metadata("MyModule")
>>> m.set("data_length", 42)
>>> m.get("data_length")
42

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
"MyModule"
"""


import json


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
    def __init__(self, module_identifier="main"):
        """
        :param module_identifier: string that uniquely identifies the
                                  current module. Default main.
        """
        self.metadata = {}
        self.module = 'main'
        self.set("version", 2)
        self.set("data", {})
        self.set("module", None)
        self.set_module(module_identifier)

    def set_module(self, identifier):
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
                raise Exception("This metadata was already " \
                                + "initialized for module '%s'."
                                % self.metadata["module"])
        # save module identifier
        self.module = identifier

    def get_module(self):
        """
        get identifier string of the current active module
        :return: string that identifies the current active module
        """
        return self.module

    def set(self, key, value):
        """
        stores a key value pair
        :param key: the key which itentifies the content
        :param value: value to store
        """
        if self.module == 'main':
            # if in main context, store it in root
            self.metadata[key] = value
        else:
            # otherwise store value in module hierarchie
            self.metadata["data"][key] = value

    def get(self, key):
        """
        returns the value for a given key
        :param key: the key which itentifies the content
        :return: stored value
        """
        # TODO: figure out if we shall throw an exception
        #       or simply return None if key wasn't found
        if self.module == "main":
            if key not in self.metadata:
                raise KeyError("Key '%s' not found in metadata" % key)
            return self.metadata[key]
        else:
            if key not in self.metadata["data"]:
                raise KeyError("Key '%s' not found in modules metadata" % key)
            return self.metadata["data"][key]

    def read(self, instream):
        """
        reads json formatted content from stream.

        This will overwrite all content previously stored as metadata.
        The currently selected module will change to 'main'
        :param stream: stream to read from
        """
        self.metadata = json.loads(instream.read())
        self.module = 'main'

    def write(self, outstream):
        """
        writes the current metadata into a stream
        """
        # check if some information are missing
        if self.metadata["module"] is None:
            raise InformationMissingError("Module identifier is missing")
        if "version" not in self.metadata:
            raise InformationMissingError("Metadata version is missing")

        # write metadata to stream
        outstream.write(json.dumps(self.metadata))
        outstream.flush()
