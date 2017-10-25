from construct import Bitwise, Pass, Mapping, Int16ul, Int32ul
from Int12ul import Int12ul


def ClusterAddress12Bit():
    """
    Mapping of a FAT12 File Allocation Table Entry
    """
    # subcon = Bitwise(Int12ul())
    subcon = Int16ul
    default = Pass
    mapping = {}
    mapping[0x0] = 'free_cluster'
    mapping[0x1] = 'last_cluster'
    mapping[0xff7] = 'bad_cluster'
    for i in range(0xff8, 0xfff + 1):
        mapping[i] = 'last_cluster'

    encmapping = mapping.copy()
    encmapping.update({v: v for v in mapping.values()})

    return Mapping(subcon,
                   encoding=encmapping,
                   decoding=mapping,
                   encdefault=default,
                   decdefault=default,
                   )


def ClusterAddress16Bit():
    """
    Mapping of a FAT16 File Allocation Table Entry
    """
    subcon = Int16ul
    default = Pass
    mapping = {}
    mapping[0x0] = 'free_cluster'
    mapping[0x1] = 'last_cluster'
    mapping[0xfff7] = 'bad_cluster'
    for i in range(0xfff8, 0xffff + 1):
        mapping[i] = 'last_cluster'

    encmapping = mapping.copy()
    encmapping.update({v: v for v in mapping.values()})

    return Mapping(subcon,
                   encoding=encmapping,
                   decoding=mapping,
                   encdefault=default,
                   decdefault=default,
                   )


def ClusterAddress32Bit():
    """
    Mapping of a FAT32 File Allocation Table Entry
    """
    subcon = Int32ul
    default = Pass
    mapping = {}
    mapping[0x0] = 'free_cluster'
    mapping[0x1] = 'last_cluster'
    mapping[0xffffff7] = 'bad_cluster'
    for i in range(0xffffff8, 0xfffffff + 1):
        mapping[i] = 'last_cluster'

    encmapping = mapping.copy()
    encmapping.update({v: v for v in mapping.values()})

    return Mapping(subcon,
                   encoding=encmapping,
                   decoding=mapping,
                   encdefault=default,
                   decdefault=default,
                   )


FAT12Entry = ClusterAddress12Bit()

FAT16Entry = ClusterAddress16Bit()

FAT32Entry = ClusterAddress32Bit()
