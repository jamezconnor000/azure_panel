"""
Loom TLV Codec
Tag-Length-Value encoding/decoding for AetherDB binary format.
"""

import struct
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .schema_registry import FieldDef, FieldType, TableDef, get_schema
from .errors import TranslationError, TranslationErrorType, ErrorSeverity, Direction


class TLVCodec:
    """
    Tag-Length-Value codec for AetherDB binary format.

    TLV Format:
    - Tag: 2 bytes (uint16) - field ID from schema
    - Length: 2 bytes (uint16) - length of value in bytes
    - Value: variable bytes - encoded field value
    """

    # Type encoders/decoders
    TYPE_FORMATS = {
        FieldType.UINT8: ("B", 1),
        FieldType.UINT16: ("<H", 2),
        FieldType.UINT32: ("<I", 4),
        FieldType.UINT64: ("<Q", 8),
        FieldType.INT8: ("b", 1),
        FieldType.INT16: ("<h", 2),
        FieldType.INT32: ("<i", 4),
        FieldType.INT64: ("<q", 8),
        FieldType.FLOAT32: ("<f", 4),
        FieldType.FLOAT64: ("<d", 8),
        FieldType.BOOL: ("?", 1),
    }

    def encode_record(self, schema: TableDef, data: Dict[str, Any]) -> bytes:
        """
        Encode a dictionary to TLV binary format.

        Args:
            schema: Table schema definition
            data: Dictionary of field name -> value

        Returns:
            Encoded binary data
        """
        result = bytearray()

        # Validate required fields
        for field in schema.get_required_fields():
            if field.name not in data or data[field.name] is None:
                raise TranslationError(
                    error_type=TranslationErrorType.MISSING_REQUIRED,
                    direction=Direction.SQL_TO_BINARY,
                    table=schema.name,
                    field_name=field.name,
                    message=f"Required field '{field.name}' is missing",
                    suggested_fix=f"Provide a value for '{field.name}'"
                )

        # Encode each field
        for field_name, value in data.items():
            field = schema.get_field(field_name)
            if field is None:
                # Unknown field, skip
                continue

            if value is None:
                # Null values are not encoded
                continue

            try:
                encoded_value = self._encode_value(field, value)
                tag = struct.pack("<H", field.id)
                length = struct.pack("<H", len(encoded_value))
                result.extend(tag)
                result.extend(length)
                result.extend(encoded_value)
            except Exception as e:
                raise TranslationError(
                    error_type=TranslationErrorType.ENCODING_ERROR,
                    direction=Direction.SQL_TO_BINARY,
                    table=schema.name,
                    field_name=field.name,
                    message=f"Failed to encode field '{field.name}': {str(e)}",
                    source_data={field.name: value},
                    root_cause=str(e),
                    suggested_fix="Check field value type matches schema"
                )

        return bytes(result)

    def decode_record(self, schema: TableDef, data: bytes) -> Dict[str, Any]:
        """
        Decode TLV binary to dictionary.

        Args:
            schema: Table schema definition
            data: Binary TLV data

        Returns:
            Dictionary of field name -> value
        """
        result = {}
        offset = 0

        while offset < len(data):
            if offset + 4 > len(data):
                raise TranslationError(
                    error_type=TranslationErrorType.DECODING_ERROR,
                    direction=Direction.BINARY_TO_SQL,
                    table=schema.name,
                    message="Truncated TLV header",
                    suggested_fix="Data may be corrupted, verify source"
                )

            # Read tag and length
            tag = struct.unpack("<H", data[offset:offset+2])[0]
            length = struct.unpack("<H", data[offset+2:offset+4])[0]
            offset += 4

            if offset + length > len(data):
                raise TranslationError(
                    error_type=TranslationErrorType.DECODING_ERROR,
                    direction=Direction.BINARY_TO_SQL,
                    table=schema.name,
                    message=f"Truncated TLV value for tag {tag}",
                    suggested_fix="Data may be corrupted, verify source"
                )

            # Read value
            value_bytes = data[offset:offset+length]
            offset += length

            # Find field definition
            field = schema.get_field_by_id(tag)
            if field is None:
                # Unknown tag, skip (forward compatibility)
                continue

            try:
                value = self._decode_value(field, value_bytes)
                result[field.name] = value
            except Exception as e:
                raise TranslationError(
                    error_type=TranslationErrorType.DECODING_ERROR,
                    direction=Direction.BINARY_TO_SQL,
                    table=schema.name,
                    field_name=field.name,
                    message=f"Failed to decode field '{field.name}': {str(e)}",
                    root_cause=str(e),
                    suggested_fix="Check binary data integrity"
                )

        # Apply defaults for missing fields
        for field in schema.fields:
            if field.name not in result and field.default is not None:
                result[field.name] = field.default

        return result

    def _encode_value(self, field: FieldDef, value: Any) -> bytes:
        """Encode a single field value."""
        field_type = field.field_type

        if field_type in self.TYPE_FORMATS:
            fmt, _ = self.TYPE_FORMATS[field_type]
            return struct.pack(fmt, value)

        elif field_type == FieldType.STRING:
            encoded = value.encode("utf-8")
            if field.max_length and len(encoded) > field.max_length:
                encoded = encoded[:field.max_length]
            return encoded

        elif field_type == FieldType.BYTES:
            if field.max_length and len(value) > field.max_length:
                value = value[:field.max_length]
            return bytes(value)

        elif field_type == FieldType.TIMESTAMP:
            # Store as microseconds since epoch
            if isinstance(value, datetime):
                ts = int(value.timestamp() * 1_000_000)
            elif isinstance(value, (int, float)):
                ts = int(value * 1_000_000)
            else:
                raise ValueError(f"Invalid timestamp: {value}")
            return struct.pack("<Q", ts)

        elif field_type == FieldType.ARRAY:
            return self._encode_array(field, value)

        else:
            raise ValueError(f"Unsupported field type: {field_type}")

    def _decode_value(self, field: FieldDef, data: bytes) -> Any:
        """Decode a single field value."""
        field_type = field.field_type

        if field_type in self.TYPE_FORMATS:
            fmt, _ = self.TYPE_FORMATS[field_type]
            return struct.unpack(fmt, data)[0]

        elif field_type == FieldType.STRING:
            return data.decode("utf-8")

        elif field_type == FieldType.BYTES:
            return bytes(data)

        elif field_type == FieldType.TIMESTAMP:
            ts = struct.unpack("<Q", data)[0]
            return datetime.fromtimestamp(ts / 1_000_000)

        elif field_type == FieldType.ARRAY:
            return self._decode_array(field, data)

        else:
            raise ValueError(f"Unsupported field type: {field_type}")

    def _encode_array(self, field: FieldDef, values: List[Any]) -> bytes:
        """Encode an array field."""
        if field.array_of is None:
            raise ValueError(f"Array field {field.name} has no element type")

        result = bytearray()
        # Array header: element count (4 bytes)
        result.extend(struct.pack("<I", len(values)))

        if field.array_of in self.TYPE_FORMATS:
            fmt, size = self.TYPE_FORMATS[field.array_of]
            for val in values:
                result.extend(struct.pack(fmt, val))
        else:
            # Variable length elements (strings, etc.)
            for val in values:
                if field.array_of == FieldType.STRING:
                    encoded = val.encode("utf-8")
                    result.extend(struct.pack("<H", len(encoded)))
                    result.extend(encoded)
                else:
                    raise ValueError(f"Unsupported array element type: {field.array_of}")

        return bytes(result)

    def _decode_array(self, field: FieldDef, data: bytes) -> List[Any]:
        """Decode an array field."""
        if field.array_of is None:
            raise ValueError(f"Array field {field.name} has no element type")

        count = struct.unpack("<I", data[:4])[0]
        offset = 4
        result = []

        if field.array_of in self.TYPE_FORMATS:
            fmt, size = self.TYPE_FORMATS[field.array_of]
            for _ in range(count):
                val = struct.unpack(fmt, data[offset:offset+size])[0]
                result.append(val)
                offset += size
        else:
            for _ in range(count):
                if field.array_of == FieldType.STRING:
                    length = struct.unpack("<H", data[offset:offset+2])[0]
                    offset += 2
                    val = data[offset:offset+length].decode("utf-8")
                    result.append(val)
                    offset += length
                else:
                    raise ValueError(f"Unsupported array element type: {field.array_of}")

        return result


# Convenience functions
def encode_record(table_name: str, data: Dict[str, Any]) -> bytes:
    """Encode a record for a named table."""
    schema = get_schema(table_name)
    if schema is None:
        raise ValueError(f"Unknown table: {table_name}")
    codec = TLVCodec()
    return codec.encode_record(schema, data)


def decode_record(table_name: str, data: bytes) -> Dict[str, Any]:
    """Decode a record for a named table."""
    schema = get_schema(table_name)
    if schema is None:
        raise ValueError(f"Unknown table: {table_name}")
    codec = TLVCodec()
    return codec.decode_record(schema, data)
