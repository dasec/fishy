"""
FAT12, FAT16 and FAT32 Cluster address definition.
"""
from construct import Pass, Mapping, Int16ul, Int32ul

# As construct.Enum does not allow multiple integers mapping to one value,
# these cluster address definitions are implemented by imitation the
# construct.Enum function and returning a valid construct.Mapping instance.


def get_12_bit_cluster_address() -> Mapping:
    """
    Mapping of a FAT12 File Allocation Table Entry
    :note: don't use this Mapping to generate the actual bytes to store on
           filesystem, because they might depend on the next or previous value
    :rtype: construct.Mapping
    """
    # subcon = Bitwise(Int12ul())
    subcon = Int16ul
    default = Pass
    mapping = dict()
    mapping[0x0] = 'free_cluster'
    mapping[0x1] = 'last_cluster'
    mapping[0xff7] = 'bad_cluster'
    for i in range(0xff8, 0xfff + 1):
        mapping[i] = 'last_cluster'

    encmapping = mapping.copy()
    encmapping['free_cluster'] = 0x000
    encmapping['bad_cluster'] = 0xff7
    encmapping['last_cluster'] = 0xfff

    return Mapping(subcon,
                   encoding=encmapping,
                   decoding=mapping,
                   encdefault=default,
                   decdefault=default,
                  )


def get_16_bit_cluster_address() -> Mapping:
    """
    Mapping of a FAT16 File Allocation Table Entry
    :rtype: construct.Mapping
    """
    subcon = Int16ul
    default = Pass
    mapping = dict()
    mapping[0x0] = 'free_cluster'
    mapping[0x1] = 'last_cluster'
    mapping[0xfff7] = 'bad_cluster'
    for i in range(0xfff8, 0xffff + 1):
        mapping[i] = 'last_cluster'

    encmapping = mapping.copy()
    encmapping['free_cluster'] = 0x0000
    encmapping['bad_cluster'] = 0xfff7
    encmapping['last_cluster'] = 0xffff

    return Mapping(subcon,
                   encoding=encmapping,
                   decoding=mapping,
                   encdefault=default,
                   decdefault=default,
                  )


def get_32_bit_cluster_address() -> Mapping:
    """
    Mapping of a FAT32 File Allocation Table Entry
    :rtype: construct.Mapping
    """
    subcon = Int32ul
    default = Pass
    mapping = dict()
    mapping[0x0] = 'free_cluster'
    mapping[0x1] = 'last_cluster'
    mapping[0xffffff7] = 'bad_cluster'
    for i in range(0xffffff8, 0xfffffff + 1):
        mapping[i] = 'last_cluster'

    encmapping = mapping.copy()
    encmapping['free_cluster'] = 0x0000000
    encmapping['bad_cluster'] = 0xffffff7
    encmapping['last_cluster'] = 0xfffffff

    return Mapping(subcon,
                   encoding=encmapping,
                   decoding=mapping,
                   encdefault=default,
                   decdefault=default,
                  )


FAT12Entry = get_12_bit_cluster_address()

FAT16Entry = get_16_bit_cluster_address()

FAT32Entry = get_32_bit_cluster_address()
