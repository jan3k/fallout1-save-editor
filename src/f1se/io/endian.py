"""Big-endian helpers for Fallout 1 save files."""
from __future__ import annotations


def require_range(data: bytes | bytearray, offset: int, size: int) -> None:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError(f"read/write outside buffer: offset=0x{offset:X}, size={size}, len=0x{len(data):X}")


def u16be(data: bytes | bytearray, offset: int) -> int:
    require_range(data, offset, 2)
    return int.from_bytes(data[offset:offset + 2], "big", signed=False)


def i16be(data: bytes | bytearray, offset: int) -> int:
    require_range(data, offset, 2)
    return int.from_bytes(data[offset:offset + 2], "big", signed=True)


def u32be(data: bytes | bytearray, offset: int) -> int:
    require_range(data, offset, 4)
    return int.from_bytes(data[offset:offset + 4], "big", signed=False)


def i32be(data: bytes | bytearray, offset: int) -> int:
    require_range(data, offset, 4)
    return int.from_bytes(data[offset:offset + 4], "big", signed=True)


def put_i32be(data: bytearray, offset: int, value: int) -> bytes:
    require_range(data, offset, 4)
    old = bytes(data[offset:offset + 4])
    data[offset:offset + 4] = int(value).to_bytes(4, "big", signed=True)
    return old


def put_u32be(data: bytearray, offset: int, value: int) -> bytes:
    require_range(data, offset, 4)
    old = bytes(data[offset:offset + 4])
    data[offset:offset + 4] = int(value).to_bytes(4, "big", signed=False)
    return old


def c_string(data: bytes | bytearray, offset: int, size: int) -> str:
    require_range(data, offset, size)
    chunk = bytes(data[offset:offset + size])
    return chunk.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def hex_slice(data: bytes | bytearray, offset: int, size: int) -> str:
    require_range(data, offset, size)
    return bytes(data[offset:offset + size]).hex()
