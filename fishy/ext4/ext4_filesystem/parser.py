import builtins
import time

class Parser:
    @staticmethod
    def parse(image, offset, length, structure, byteorder='little'):
        data_dict = {}
        image.seek(offset)

        data = image.read(length)
        for key in structure:
            offset = structure[key]['offset']
            size = structure[key]['size']

            bytes = data[offset:offset+size]
            value = int.from_bytes(bytes, byteorder=byteorder)

            if "format" in structure[key]:
                if structure[key]["format"] == "ascii":
                    value = bytes.decode('ascii')
                elif structure[key]["format"] == "raw":
                    value = bytes
                elif structure[key]["format"] == "time":
                    value = time.gmtime(value)
                else:
                    form = getattr(builtins, structure[key]["format"])
                    value = form(value)

            data_dict[key] = value
        return data_dict