# This class contains code under Copyright (c) by 2017 Jonas Plum licensed through MIT Licensing

from fishy.APFS.APFS_filesystem.APFS_Parser import Parser


# Nodes, especially entry area (including the currently defunct extended fields) could use some more work, possible to
# split entries into their own class(es) for better visual representation

class Node:

# Nodestructure is still based on older reference sheet; important parts are still right

    nodestructure = {
        "node_type": {"offset": 0x0, "size": 2},
        "level": {"offset": 0x2, "size": 2},
        "entry_count": {"offset": 0x4, "size": 4},
        "reserved1": {"offset": 0x8, "size": 2}, # fill with data
        "keys_offset": {"offset": 0xA, "size": 2},
        "keys_length": {"offset": 0xC, "size": 2},
        "datas_offset": {"offset": 0xE, "size": 2},
        "reserved2": {"offset": 0x10, "size": 8} # fill with data


    }

    def __init__(self, fs_stream, offset, blocksize):
        self.blocksize = blocksize
        self.data = self.parseNode(fs_stream, offset)
        self.offset = offset

    def parseNode(self, fs_stream, offset):
        d = Parser.parse(fs_stream, offset+32, self.blocksize - 32, structure=self.nodestructure)

        entries = d["entry_count"]
        ehs = {}
        flags = d["node_type"]

        if flags & 4 == 0:
            for i in range(0, entries):
                eh = {
                    "key_offset " + str(i): {"offset": 0x18+(8*i), "size": 2},
                    "key_size " + str(i): {"offset": 0x1A+(8*i), "size": 2},
                    "data_offset " + str(i): {"offset": 0x1C+(8*i), "size": 2},
                    "data_size " + str(i): {"offset": 0x1E+(8*i), "size": 2}
                }
                ehs.update(eh)

        else:
            for i in range(0, entries):
                eh = {
                    "key_offset " + str(i): {"offset": 0x18+(4*i), "size": 2},
                    "data_offset " + str(i): {"offset": 0x1A+(4*i), "size": 2},
                }
                ehs.update(eh)

        entryheaders = Parser.parse(fs_stream, offset+32, self.blocksize-32, structure=ehs)

        f = {**d, **entryheaders}

        eks = {}
        entry_vals = {}

        keys_offset = f["keys_offset"]
        datas_offset = f["datas_offset"] #unused


        # if type etc
        for i in range(0, entries):
            k_offset = f["key_offset " + str(i)]
            key_hdr = {
                "oid " + str(i): {"offset": 0x18+keys_offset+k_offset, "size": 4},
                "kind " + str(i): {"offset": 0x18+keys_offset+k_offset+4, "size": 4}
            }
            kh = Parser.parse(fs_stream, offset+32, self.blocksize-32, structure=key_hdr)
            eks.update(key_hdr)
            oid = kh["oid " + str(i)] + ((kh["kind " +str(i)] & 0x0FFFFFFF) << 32)
 #            kh["oid " + str(i)] = oid does not work

            kind = kh["kind " + str(i)] >> 28
          #  kh["kind " + str(i)] = kind  does not work

            if kind == 0:  # omap entry
                omap_key_hdr = {
                    "xid " + str(i): {"offset": 0x18+keys_offset+k_offset+8, "size": 8}
                }
                key_hdr.update(omap_key_hdr)
                eks.update(key_hdr)

                d_offset = f["data_offset " + str(i)]
                omap_val = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))
                    "omv_flags " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 4,
                                            "format": "hex"},
                    "omv_size " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 4, "size": 4},
                    "omv_paddr " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 8, "size": 8}

                }
                entry_vals.update(omap_val)

            elif kind == 1:  # Snap Meta entry
                # Snap Meta key is empty
                eks.update(key_hdr)

                d_offset = f["data_offset " + str(i)]
                snap_val = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))
                    "extentref_tree_oid " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1),
                                                     "size": 8},
                    "sblock_oid " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 8, "size": 8},
                    "create_time " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 16, "size": 8},
                    "change_time " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 24, "size": 8},
                    "inum " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 32, "size": 8},
                    "extentref_tree_type " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 *(flags & 1) + 40,
                                                      "size": 4},
                    "flags " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 *(flags & 1) + 44, "size": 4},
                    "name_len " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 *(flags & 1) + 48, "size": 2},
                    "name " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 *(flags & 1) + 50, "size": 2,
                                       "format": "utf"}

                    #TODO testen/anpassen
                }
                entry_vals.update(snap_val)

            elif kind == 2:  # Type Extent entry
                # Extent Type key is empty
                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]

                phys_extent_entry = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))
                    "block_count " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 4},
                    "obj_kind " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 4, "size": 2},
                    "block_size " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 6, "size": 2},
                    "owning_oid " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 8, "size": 8},
                    # owning id can be inode value private id or xattr key record identifier
                    "refcnt " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 16, "size": 4}
                }
                entry_vals.update(phys_extent_entry)

                # TODO implement j_obj_kind into this via reading "obj kind" (see j_obj_kind in official documentation)

            elif kind == 3:  # Inode entry
                # Inode key is empty; obj id in key header is inode number
                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]

                inode_entry = {
                                                #Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))
                    "parent_id " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 8},
                    "private_id " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 8, "size": 8},
                    "create_time " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 16, "size": 8,
                                              "format": "hex"
                                              },
                    "mod_time " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 24, "size": 8,
                                              "format": "hex"
                                              },
                    "change_time " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 32, "size": 8,
                                              "format": "hex"
                                              },
                    "access_time " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 40, "size": 8,
                                              "format": "hex"
                                              },

                    # TODO: timer test time format; adjust time format if necessary

                    "internal_flags " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 48,
                                                 "size": 8},
                    "nchildren_or_nlink " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 56,
                                                     "size": 4},
                    "def_proctection_class " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 60,
                                                        "size": 4},
                    "write_gen_counter " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 64,
                                                    "size": 4},
                    "bsd_flags " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 68, "size": 4},
                    "owner " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 72, "size": 4},
                    "group " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 76, "size": 4},
                    "mode " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 80, "size": 2},
                    "pad1 " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 82, "size": 2},
                    "pad2 " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 84, "size": 8}

                }

                # TODO extended fields

                xf_blob = {
                    "xf_num_exts " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 92,
                                              "size": 2},
                    "xf_used_data " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 94,
                                               "size": 2}
                }
                inode_entry.update(xf_blob)

                temp = Parser.parse(fs_stream, offset + 32, self.blocksize - 32, structure=xf_blob)

                xfields_nr = temp["xf_num_exts " + str(i)]

                xfields = {}

                prev_size = 0

                xfield_offset = []  # array variant, used data + header
                # xfield_offset # integer variant, used data + header


                for j in range(0, xfields_nr):
                    xfield_hdr = {
                        "x_type " + str(i) + " " + str(j): {
                            "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (j * 4), "size": 1},
                        "x_flags " + str(i) + " " + str(j): {
                            "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 97 + (j * 4), "size": 1},
                        "x_size " + str(i) + " " + str(j): {
                            "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 98 + (j * 4), "size": 2}
                    }
                    xfields.update(xfield_hdr)
                    temp_type = Parser.parse(fs_stream, offset + 32, self.blocksize - 32, structure=xfield_hdr)
                    temp = temp_type["x_type " + str(i) + " " + str(j)]
                    size = temp_type["x_size " + str(i) + " " + str(j)]

                    # if j <= xfields nr & if size (n % 8) -> padding mit size n = (n + (8- n % 8)) - size
                    # prev size =
                    if j > 0:
                        prev = Parser.parse(fs_stream, offset + 32, self.blocksize - 32, structure=xfields)

                        temps = prev["x_size " + str(i) + " " + str(j-1)]

                        if (temps % 8):
                            prev_size += temps + (8 - temps % 8)
                        else:
                            prev_size += temps

                    if temp == 1:
                        sibling_snap_id = {
                            "reserved_s_s_id " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size,
                                "size": size
                            }
                        }
                        xfields.update(sibling_snap_id)

                        if (size % 8):
                            sibling_snap_padding = {"padding_s_s_id " +str(i)+" "+str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size
                                          + size,
                                "size": (size +(8 - size % 8)) - size,
                                "format": "raw"
                            }}
                            xfields.update(sibling_snap_padding)

                    if temp == 2:
                        delta_tree_id = {
                            "reserved_d_t_id " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size,
                                "size": size
                            }
                        }
                        xfields.update(delta_tree_id)

                        if (size % 8):
                            delta_tree_padding = {"padding_d_t_id " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size
                                          + size,
                                "size": (size + (8 - size % 8)) - size,
                                "format": "raw"

                            }}
                            xfields.update(delta_tree_padding)

                    if temp == 3:
                        doc_id = {
                            "reserved_doc_id " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size,
                                "size": size
                            }
                        }
                        xfields.update(doc_id)

                        if (size % 8):
                            doc_padding = {"padding_doc_id " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size
                                          + size,
                                "size": (size + (8 - size % 8)) - size,
                                "format": "raw"

                            }}
                            xfields.update(doc_padding)

                    if temp == 4:
                        name = {
                            "name " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size,
                                "size": size, "format": "utf"
                            }
                        }
                        xfields.update(name)
                        if (size % 8):
                            name_padding = {"padding_name " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size
                                          + size,
                                "size": (size + (8 - size % 8)) - size,
                                "format": "raw"

                            }}
                            xfields.update(name_padding)

                    if temp == 8:
                        fsize = {
                            "fsize " +str(i) + " " +str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size,
                                "size": 8
                                          },
                            "reserved_fsize1 " + str(i) + " " + str(j):{
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size
                                          + 8,
                                "size": 8
                            },
                            "reserved_fsize2 " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (
                                            xfields_nr * 4) + prev_size
                                          + 16,
                                "size": 8
                            },
                            "reserved_fsize3 " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (
                                            xfields_nr * 4) + prev_size
                                          + 24,
                                "size": 8
                            },
                            "reserved_fsize4 " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (
                                            xfields_nr * 4) + prev_size
                                          + 32,
                                "size": 8
                            }
                        }
                        xfields.update(fsize)
                        if (size % 8):
                            fsize_padding = {"fsize_name " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4) + prev_size
                                          + size,
                                "size": (size + (8 - size % 8)) - size,
                                "format": "raw"

                            }}
                            xfields.update(fsize_padding)

                    if temp == 6 or temp == 7 or temp == 9 or temp == 10 or temp == 11 or temp == 12 or temp == 13 \
                            or temp == 14:
                        tempxfield = {
                            "temp_xfield " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size,
                                "size": size
                            }
                        }
                        xfields.update(tempxfield)

                        if (size % 8):
                            tempxfieldpadding = {"padding_temp_xfield " + str(i) + " " + str(j): {
                                "offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 96 + (xfields_nr * 4)
                                          + prev_size
                                          + size,
                                "size": (size + (8 - size % 8)) - size,
                                "format": "raw"

                            }}
                            xfields.update(tempxfieldpadding)




                # TODO: MOST EXTENDED FIELDS NOT IMPLEMENTED; MISSING INFORMATION; ALSO NON IMPLEMENTED FOR DREC Entry
                # TODO: check if padding is right -> is there padding if a single extended field is present?
                inode_entry.update(xfields)
                entry_vals.update(inode_entry)

            elif kind == 4:  # xattr entry
                xattr_key_hdr_len = {
                    "name_len " + str(i): {"offset": 0x18+keys_offset+k_offset+8, "size": 2},
                }

                temp = Parser.parse(fs_stream, offset+32, self.blocksize-32, structure=xattr_key_hdr_len)
                size = temp["name_len " + str(i)]

                xattr_key_hdr = {
                    "name_len " + str(i): {"offset": 0x18 + keys_offset + k_offset+10, "size": 2},
                    "name " + str(i): {"offset": 0x18 + keys_offset + k_offset + 12, "size": size, "format": "utf"}
                }

                key_hdr.update(xattr_key_hdr)

                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]
                xattr_entry_start = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))

                    "xa_type " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 2},
                    "xa_length " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 2, "size": 2}
                }

                temp = Parser.parse(fs_stream, offset + 32, self.blocksize - 32, structure=xattr_entry_start)
                length = temp["xa_length " + str(i)]

                xattr_entry_cont = {
                    "data " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 4, "size": length},
                }

                xattr_entry = {**xattr_entry_start, **xattr_entry_cont}

                entry_vals.update(xattr_entry)


            elif kind == 5:  # sibling entry
                sibling_key_hdr = {
                    "sibling_id " + str(i): {"offset": 0x18+keys_offset+k_offset+8, "size": 8}
                }
                key_hdr.update(sibling_key_hdr)

                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]

                sibling_entry_start = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))

                    "parent_id " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 8},
                    "name_len " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 8, "size": 2},
                }

                temp = Parser.parse(fs_stream, offset+32, self.blocksize-32, structure=sibling_entry_start)
                length = temp["name_len " +str(i)]

                sibling_entry_cont = {
                    "name " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 10, "size": length,
                                       "format": "utf"}
                }

                sibling_entry = {**sibling_entry_start, **sibling_entry_cont}

                entry_vals.update(sibling_entry)


            elif kind == 6:  # extent status / dstream entry
                # dstream key empty

                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]
                dstream_entry = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))

                    "refcount " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 4}
                }

                entry_vals.update(dstream_entry)


            elif kind == 7:  # Crypto state entry
                eks.update(key_hdr)
                # Crypto key empty
                d_offset = f["data_offset " + str(i)]
                crypto_entry = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))

                    "refcount " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 4},
                    # TODO: implement complete crypto state; might not actually be correct size as last part is array
                    "crypto_state " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1)+4, "size": 32}
                }
                entry_vals.update(crypto_entry)


            elif kind == 8:  # file extent entry
                file_extent_key = {
                    "physical_address " +str(i): {"offset": 0x18+keys_offset+k_offset+8, "size": 8}
                }
                key_hdr.update(file_extent_key)

                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]
                file_extent_value = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))

                    "length " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 8},
                    "paddr_block_num " + str(i):{"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1) + 8, "size": 8},
                    "flags " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1)+16, "size": 8}
                }

                entry_vals.update(file_extent_value)


            elif kind == 9:  # drec entry

                drec_key_hdr_name_len = {
                    "name_len " + str(i): {"offset": 0x18+keys_offset+k_offset+8, "size": 1}
                }
                temp = Parser.parse(fs_stream, offset + 32, self.blocksize - 32, structure=drec_key_hdr_name_len)
                size = temp["name_len " + str(i)]

                drec_key_hdr = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))

                    "name_len " + str(i): {"offset": 0x18+keys_offset+k_offset+8, "size": 1},
                    "hash " + str(i): {"offset": 0x18+keys_offset+k_offset+9, "size": 3},
                    "name " + str(i): {"offset": 0x18+keys_offset+k_offset+12, "size": size, "format": "utf"}
                }
                key_hdr.update(drec_key_hdr)

                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]
                drec_entry_start = {
                    "file_id " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 8},
                    "date_added " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1)+8, "size": 8}
                }
                entry_vals.update(drec_entry_start)

                # TODO: add xf_blob (like inode) -> extended fields; testing implies structure may be different from
                # TODO\2 inode extended fields


            elif kind == 10: # dstats entry
                # directory stats key is empty
                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]
                dstats_entry = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))

                    "num_children " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 8},
                    "total_size " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1)+8, "size": 8},
                    "chained_key " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1)+16, "size": 8},
                    "gen_count " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1)+24, "size": 8}
                }

                entry_vals.update(dstats_entry)


            elif kind == 11:  # snap name entry
                snap_name_key_hdr_len = {
                    "name_len " + str(i): {"offset": 0x18+keys_offset+k_offset+8, "size": 2},
                }
                temp = Parser.parse(fs_stream, offset+32, self.blocksize - 32, structure=snap_name_key_hdr_len)
                size = temp["name_len " + str(i)]

                snap_name_key_hdr = {

                    "name_len " + str(i): {"offset": 0x18 + keys_offset + k_offset + 8, "size": 2},
                    "name " + str(i): {"offset": 0x18 + keys_offset + k_offset + 8 + 2, "size": size, "format": "utf"}
                }

                key_hdr.update(snap_name_key_hdr)
                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]
                snap_name_val = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))

                    "xid " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 8}
                }
                entry_vals.update(snap_name_val)


            elif kind == 12:  # sibling map entry
                # sibling map key is empty; oid from key header matches sibling id from sibling key t
                eks.update(key_hdr)
                d_offset = f["data_offset " + str(i)]
                sibling_map_entry = {
                    # Copyright (c) by 2017 Jonas Plum (- 40 * (flags & 1))

                    "file_id " + str(i): {"offset": self.blocksize - 32 - d_offset - 40 * (flags & 1), "size": 8}
                }

                entry_vals.update(sibling_map_entry)


        entrykeys = Parser.parse(fs_stream, offset+32, self.blocksize - 32, structure=eks)
        g = {**f, **entrykeys}


        entry_values_p = Parser.parse(fs_stream, offset+32, self.blocksize-32, structure=entry_vals)

        h = {**g, **entry_values_p}

        return h


    def getVolumeMapping(self):

        entries = self.data["entry_count"]
        VolumeMapping = []
        for i in range(0, entries):
            if self.data["kind " + str(i)] == 0:
                singleMapping = (self.data["omv_paddr " + str(i)], self.data["oid " + str(i)])
                VolumeMapping.append(singleMapping)
            else:
                error = self.data["kind "+str(i)]
                raise TypeError(error)
        return VolumeMapping

