from construct import Construct, bits2integer, FieldError


class Int12ul(Construct):
    """
    Unsigned, little endian 12-bit integer

    Needs to be wrapped into a Bitwise object
    _build is not implemented, as this whould require, that
    the second value is already known
    """

    skipped_third_nibble = ''

    def _sizeof(self, context, path):
        return 12

    def _parse(self, stream, context, path):
        """
        read a 12 bit little endian value from stream
        """
        # as 12 bit little endian values are stored like:
        # nibbleV1 nibbleV1 nibbleV2 nibbleV1 nibbleV2 nibbleV2
        # we need to store the third nibble on every V1
        # and prepend it on every V2
        if Int12ul.skipped_third_nibble == '':
            # read first byte
            data = stream.read(8)
            # skip third nibble
            Int12ul.skipped_third_nibble = stream.read(4)
            # read last nibble and prepend to data
            data = stream.read(4) + data
        else:
            data = Int12ul.skipped_third_nibble + stream.read(8)
            Int12ul.skipped_third_nibble = ''
        if len(data) != 12:
            raise FieldError("could not read enough bytes, expected %d, \
                    found %d" % (12, len(data)))
        value = bits2integer(data)
        return value
