from typing import Union


def check_dict_has_certain_keys(
    dict_obj: dict, keys: Union[list[str], tuple[str, ...]], exception_obj: Exception
) -> None:
    """
    Check if dict has certain keys.

    Args:
        dict_obj: dict object.
        keys: list of keys.

    Returns:
        True if dict has all keys, False if not.
    """
    missing_keys = [key for key in keys if key not in dict_obj]
    if missing_keys:
        raise exception_obj(missing_keys)
