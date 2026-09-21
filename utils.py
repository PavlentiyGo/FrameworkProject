from collections.abc import Callable


InputFunction = Callable[[str], str]


def input_non_empty(
    prompt: str,
    input_function: InputFunction = input,
) -> str:
    while True:
        value = input_function(prompt).strip()
        if value:
            return value
        print("Значение не может быть пустым.")


def input_int(
    prompt: str,
    minimum: int | None = None,
    maximum: int | None = None,
    input_function: InputFunction = input,
) -> int:
    while True:
        try:
            value = int(input_function(prompt))
            if minimum is not None and value < minimum:
                raise ValueError
            if maximum is not None and value > maximum:
                raise ValueError
            return value
        except ValueError:
            print("Введите корректное целое число в допустимом диапазоне.")


def input_float(
    prompt: str,
    minimum: float | None = None,
    input_function: InputFunction = input,
) -> float:
    while True:
        raw_value = input_function(prompt).replace(",", ".")
        try:
            value = float(raw_value)
            if minimum is not None and value < minimum:
                raise ValueError
            return value
        except ValueError:
            print("Введите корректное число в допустимом диапазоне.")


def input_choice(
    prompt: str,
    choices: tuple[str, ...],
    input_function: InputFunction = input,
) -> str:
    while True:
        value = input_function(prompt).strip()
        if value in choices:
            return value
        print(f"Допустимые значения: {', '.join(choices)}.")
