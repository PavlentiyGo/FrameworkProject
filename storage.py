import json
from pathlib import Path

from devices import Device


def load_devices(filename: str | Path) -> list[Device]:
    path = Path(filename)
    if not path.exists():
        return []

    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Файл {path} содержит некорректный JSON"
        ) from error
    except OSError as error:
        raise RuntimeError(f"Не удалось прочитать файл {path}") from error

    if not isinstance(data, list) or not all(
        isinstance(item, dict) for item in data
    ):
        raise RuntimeError("Файл данных должен содержать список устройств")
    return data


def save_devices(filename: str | Path, devices: list[Device]) -> None:
    path = Path(filename)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(devices, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except OSError as error:
        raise RuntimeError(f"Не удалось сохранить файл {path}") from error
