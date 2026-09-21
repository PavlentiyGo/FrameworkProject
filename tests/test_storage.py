from pathlib import Path

import pytest

from devices import Device
from storage import load_devices, save_devices


def test_save_and_load_devices(
    tmp_path: Path,
    sample_devices: list[Device],
) -> None:
    filename = tmp_path / "nested" / "devices.json"

    save_devices(filename, sample_devices)

    assert load_devices(filename) == sample_devices


def test_missing_file_returns_empty_list(tmp_path: Path) -> None:
    assert load_devices(tmp_path / "missing.json") == []


def test_invalid_json_raises_data_file_error(tmp_path: Path) -> None:
    filename = tmp_path / "devices.json"
    filename.write_text("not-json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="некорректный JSON"):
        load_devices(filename)


def test_non_list_json_raises_data_file_error(tmp_path: Path) -> None:
    filename = tmp_path / "devices.json"
    filename.write_text('{"id": 1}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="список устройств"):
        load_devices(filename)
