from typing import Never


def indent(string: str) -> str:
    return "\t" + string.replace("\n", "\n\t")


type Result[T, E: Exception = Exception] = tuple[T, Never] | tuple[Never, E]


def ok[T](value: T) -> tuple[T, Never]:
    return (value, None)  # type: ignore[return-value]


def err[E: Exception](error: E, enrichment: str | None = None) -> tuple[Never, E]:
    if enrichment is not None:
        error_message = f"{enrichment}:\n{indent(str(error))}"
        error = type(error)(error_message)
        return (None, error)  # type: ignore[return-value]
    return (None, error)  # type: ignore[return-value]


def resolve_all[T](results: list[Result[T]]) -> Result[list[T], ExceptionGroup]:
    successes: list[T] = []
    errors: list[Exception] = []

    for val, error in results:
        if error is not None:
            errors.append(error)
            continue
        successes.append(val)

    if len(errors) > 0:
        messages = "\n".join(f"[{i + 1}] {e}" for i, e in enumerate(errors))
        return err(ExceptionGroup(f"Multiple errors:\n{messages}", errors))

    return ok(successes)
