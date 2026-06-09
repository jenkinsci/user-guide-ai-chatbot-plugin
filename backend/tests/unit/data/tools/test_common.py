import pytest
import json
from datetime import datetime
from data.tools.common import (
    convert_date_str_in_iso,
    datetime_serializer,
    read_json_file,
    write_json_file,
)


@pytest.mark.parametrize(
    "obj, expected, should_raise",
    [
        # 1. Naive datetime → ISO string
        (datetime(2024, 6, 15, 10, 30, 0), "2024-06-15T10:30:00", False),
        # 2. Datetime with microseconds → ISO string includes microseconds
        (datetime(2024, 1, 1, 0, 0, 0, 123456), "2024-01-01T00:00:00.123456", False),
        # 3. Midnight boundary
        (datetime(2000, 12, 31, 23, 59, 59), "2000-12-31T23:59:59", False),
        # 4. Non-serializable type (int) → TypeError
        (42, None, True),
        # 5. Non-serializable type (list) → TypeError
        (["not", "a", "date"], None, True),
    ],
)
def test_datetime_serializer(obj, expected, should_raise):
    if should_raise:
        with pytest.raises(TypeError):
            datetime_serializer(obj)
    else:
        result = datetime_serializer(obj)
        assert result == expected
        assert isinstance(result, str)


@pytest.mark.parametrize(
    "date_str, fmt, expected, should_raise",
    [
        # 1. Standard human-readable format
        ("June 15, 2024", "%B %d, %Y", "2024-06-15", False),
        # 2. Different default-format month
        ("January 01, 2000", "%B %d, %Y", "2000-01-01", False),
        # 3. Custom format (numeric)
        ("15/06/2024", "%d/%m/%Y", "2024-06-15", False),
        # 4. Invalid date string → ValueError
        ("not-a-date", "%B %d, %Y", None, True),
        # 5. Wrong format for input → ValueError
        ("2024-06-15", "%B %d, %Y", None, True),
    ],
)
def test_convert_date_str_in_iso(date_str, fmt, expected, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            convert_date_str_in_iso(date_str, fmt)
    else:
        result = convert_date_str_in_iso(date_str, fmt)
        assert result == expected
        assert isinstance(result, str)


@pytest.mark.parametrize(
    "content, expected, should_be_none",
    [
        # 1. Valid JSON object
        ('{"key": "value"}', {"key": "value"}, False),
        # 2. Valid JSON array
        ("[1, 2, 3]", [1, 2, 3], False),
        # 3. Valid nested JSON
        ('{"a": {"b": 42}}', {"a": {"b": 42}}, False),
        # 4. Malformed JSON → returns None
        ('{"bad": }', None, True),
        # 5. Empty file (invalid JSON) → returns None
        ("", None, True),
    ],
)
def test_read_json_file(tmp_path, content, expected, should_be_none):
    file = tmp_path / "test.json"
    file.write_text(content, encoding="utf-8")

    result = read_json_file(file)

    if should_be_none:
        assert result is None
    else:
        assert result == expected


def test_read_json_file_missing_file(tmp_path):
    """Reading a non-existent file returns None without raising."""
    result = read_json_file(tmp_path / "ghost.json")
    assert result is None


@pytest.mark.parametrize(
    "data, expected_keys, should_succeed",
    [
        # 1. Simple dict
        ({"name": "Alice", "age": 30}, ["name", "age"], True),
        # 2. List of dicts
        ([{"id": 1}, {"id": 2}], None, True),
        # 3. Nested structure
        ({"outer": {"inner": [1, 2, 3]}}, ["outer"], True),
        # 4. Empty dict
        ({}, None, True),
        # 5. Dict with datetime using custom serializer → succeeds
        ({"ts": datetime(2024, 6, 15, 12, 0, 0)}, ["ts"], True),
    ],
)
def test_write_json_file(tmp_path, data, expected_keys, should_succeed):
    file = tmp_path / "out" / "result.json"

    result = write_json_file(file, data, default=datetime_serializer)

    assert result is should_succeed
    assert file.exists()

    written = json.loads(file.read_text(encoding="utf-8"))
    if expected_keys:
        for key in expected_keys:
            assert key in written


def test_write_json_file_creates_parent_dirs(tmp_path):
    """write_json_file must create missing intermediate directories."""
    deep_path = tmp_path / "a" / "b" / "c" / "file.json"
    result = write_json_file(deep_path, {"x": 1})
    assert result is True
    assert deep_path.exists()
