
from collections.abc import Callable

from utils import input_choice, input_float, input_int, input_non_empty


def make_input(values: list[str]) -> Callable[[str], str]:
    iterator = iter(values)

    def fake_input(prompt: str) -> str:
        del prompt
        return next(iterator)

    return fake_input


def test_input_int_repeats_after_invalid_value() -> None:
    fake_input = make_input(["не число", "7"])

    assert input_int("Число: ", 1, 10, fake_input) == 7


def test_input_float_accepts_decimal_comma() -> None:
    fake_input = make_input(["12,5"])

    assert input_float("Цена: ", 0, fake_input) == 12.5


def test_input_non_empty_strips_spaces() -> None:
    fake_input = make_input(["   ", "  Кухня  "])

    assert input_non_empty("Помещение: ", fake_input) == "Кухня"


def test_input_choice_rejects_unknown_option() -> None:
    fake_input = make_input(["может быть", "да"])

    assert input_choice("Ответ: ", ("да", "нет"), fake_input) == "да"
