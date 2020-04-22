# -*- coding: utf-8 -*-
from pathlib import Path

import numpy as np

from asammdf import MDF, Signal, SUPPORTED_VERSIONS
import asammdf.blocks.v2_v3_blocks as v3b
import asammdf.blocks.v2_v3_constants as v3c
import asammdf.blocks.v4_blocks as v4b
import asammdf.blocks.v4_constants as v4c

SUPPORTED_VERSIONS = SUPPORTED_VERSIONS[1:]

cycles = 500
channels_count = 20
array_channels_count = 20


def get_test_data(filename=""):
    """
    Utility functions needed by all test scripts.
    """
    return Path(__file__).resolve().parent.joinpath("/data/", filename)


def generate_test_file(tmpdir, version="4.10"):
    mdf = MDF(version=version)

    if version <= "3.30":
        filename = Path(tmpdir) / f"big_test_{version}.mdf"
    else:
        filename = Path(tmpdir) / f"big_test_{version}.mf4"

    if filename.exists():
        return filename

    t = np.arange(cycles, dtype=np.float64)

    cls = v4b.ChannelConversion if version >= "4.00" else v3b.ChannelConversion

    # no conversion
    sigs = []
    for i in range(channels_count):
        sig = Signal(
            np.ones(cycles, dtype=np.uint64) * i,
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            conversion=None,
            comment="Unsigned int 16bit channel {}".format(i),
            raw=True,
        )
        sigs.append(sig)
    mdf.append(sigs, common_timebase=True)

    # linear
    sigs = []
    for i in range(channels_count):
        conversion = {
            "conversion_type": v4c.CONVERSION_TYPE_LIN
            if version >= "4.00"
            else v3c.CONVERSION_TYPE_LINEAR,
            "a": float(i),
            "b": -0.5,
        }
        sig = Signal(
            np.ones(cycles, dtype=np.int64),
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            conversion=cls(**conversion),
            comment="Signed 16bit channel {} with linear conversion".format(i),
            raw=True,
        )
        sigs.append(sig)
    mdf.append(sigs, common_timebase=True)

    # algebraic
    sigs = []
    for i in range(channels_count):
        conversion = {
            "conversion_type": v4c.CONVERSION_TYPE_ALG
            if version >= "4.00"
            else v3c.CONVERSION_TYPE_FORMULA,
            "formula": "{} * sin(X)".format(i),
        }
        sig = Signal(
            np.arange(cycles, dtype=np.int32) / 100.0,
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            conversion=cls(**conversion),
            comment="Sinus channel {} with algebraic conversion".format(i),
            raw=True,
        )
        sigs.append(sig)
    mdf.append(sigs, common_timebase=True)

    # rational
    sigs = []
    for i in range(channels_count):
        conversion = {
            "conversion_type": v4c.CONVERSION_TYPE_RAT
            if version >= "4.00"
            else v3c.CONVERSION_TYPE_RAT,
            "P1": 0,
            "P2": i,
            "P3": -0.5,
            "P4": 0,
            "P5": 0,
            "P6": 1,
        }
        sig = Signal(
            np.ones(cycles, dtype=np.int64),
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            conversion=cls(**conversion),
            comment="Channel {} with rational conversion".format(i),
            raw=True,
        )
        sigs.append(sig)
    mdf.append(sigs, common_timebase=True)

    # string
    sigs = []
    encoding = "latin-1" if version < "4.00" else "utf-8"
    for i in range(channels_count):
        sig = [
            "Channel {} sample {}".format(i, j).encode(encoding) for j in range(cycles)
        ]
        sig = Signal(
            np.array(sig),
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            comment="String channel {}".format(i),
            raw=True,
            encoding=encoding,
        )
        sigs.append(sig)
    mdf.append(sigs, common_timebase=True)

    # byte array
    sigs = []
    ones = np.ones(cycles, dtype=np.dtype("(8,)u1"))
    for i in range(channels_count):
        sig = Signal(
            ones * i,
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            comment="Byte array channel {}".format(i),
            raw=True,
        )
        sigs.append(sig)
    mdf.append(sigs, common_timebase=True)

    # value to text
    sigs = []
    ones = np.ones(cycles, dtype=np.uint64)
    conversion = {
        "raw": np.arange(255, dtype=np.float64),
        "phys": np.array(["Value {}".format(i).encode("ascii") for i in range(255)]),
        "conversion_type": v4c.CONVERSION_TYPE_TABX
        if version >= "4.00"
        else v3c.CONVERSION_TYPE_TABX,
        "links_nr": 260,
        "ref_param_nr": 255,
    }

    for i in range(255):
        conversion["val_{}".format(i)] = conversion[
            "param_val_{}".format(i)
        ] = conversion["raw"][i]
        conversion["text_{}".format(i)] = conversion["phys"][i]
    conversion["text_{}".format(255)] = "Default"

    for i in range(channels_count):
        sig = Signal(
            ones * i,
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            comment="Value to text channel {}".format(i),
            conversion=cls(**conversion),
            raw=True,
        )
        sigs.append(sig)
    mdf.append(sigs, common_timebase=True)

    name = mdf.save(filename, overwrite=True)


def generate_arrays_test_file(tmpdir):
    version = "4.10"
    mdf = MDF(version=version)
    filename = Path(tmpdir) / f"arrays_test_{version}.mf4"

    if filename.exists():
        return filename

    t = np.arange(cycles, dtype=np.float64)

    # lookup tabel with axis
    sigs = []
    for i in range(array_channels_count):
        samples = [
            np.ones((cycles, 2, 3), dtype=np.uint64) * i,
            np.ones((cycles, 2), dtype=np.uint64) * i,
            np.ones((cycles, 3), dtype=np.uint64) * i,
        ]

        types = [
            ("Channel_{}".format(i), "(2, 3)<u8"),
            ("channel_{}_axis_1".format(i), "(2, )<u8"),
            ("channel_{}_axis_2".format(i), "(3, )<u8"),
        ]

        sig = Signal(
            np.core.records.fromarrays(samples, dtype=np.dtype(types)),
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            conversion=None,
            comment="Array channel {}".format(i),
            raw=True,
        )
        sigs.append(sig)
    mdf.append(sigs, common_timebase=True)

    # lookup tabel with default axis
    sigs = []
    for i in range(array_channels_count):
        samples = [np.ones((cycles, 2, 3), dtype=np.uint64) * i]

        types = [("Channel_{}".format(i), "(2, 3)<u8")]

        sig = Signal(
            np.core.records.fromarrays(samples, dtype=np.dtype(types)),
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            conversion=None,
            comment="Array channel {} with default axis".format(i),
            raw=True,
        )
        sigs.append(sig)
    mdf.append(sigs, common_timebase=True)

    # structure channel composition
    sigs = []
    for i in range(array_channels_count):
        samples = [
            np.ones(cycles, dtype=np.uint8) * i,
            np.ones(cycles, dtype=np.uint16) * i,
            np.ones(cycles, dtype=np.uint32) * i,
            np.ones(cycles, dtype=np.uint64) * i,
            np.ones(cycles, dtype=np.int8) * i,
            np.ones(cycles, dtype=np.int16) * i,
            np.ones(cycles, dtype=np.int32) * i,
            np.ones(cycles, dtype=np.int64) * i,
        ]

        types = [
            ("struct_{}_channel_0".format(i), np.uint8),
            ("struct_{}_channel_1".format(i), np.uint16),
            ("struct_{}_channel_2".format(i), np.uint32),
            ("struct_{}_channel_3".format(i), np.uint64),
            ("struct_{}_channel_4".format(i), np.int8),
            ("struct_{}_channel_5".format(i), np.int16),
            ("struct_{}_channel_6".format(i), np.int32),
            ("struct_{}_channel_7".format(i), np.int64),
        ]

        sig = Signal(
            np.core.records.fromarrays(samples, dtype=np.dtype(types)),
            t,
            name="Channel_{}".format(i),
            unit="unit_{}".format(i),
            conversion=None,
            comment="Structure channel composition {}".format(i),
            raw=True,
        )
        sigs.append(sig)

    mdf.append(sigs, common_timebase=True)

    name = mdf.save(filename, overwrite=True)


if __name__ == "__main__":
    #    generate_test_file("3.30")
    #    generate_test_file("4.10")
    generate_arrays_test_file(r"D:\TMP")
