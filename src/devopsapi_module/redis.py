import json
from datetime import datetime
from typing import Any, Optional, Union
import redis
from module import config


ISSUE_FAMILIES_KEY = "issue_families"
PROJECT_ISSUE_CALCULATE_KEY = "project_issue_calculation"
SERVER_ALIVE_KEY = "system_all_alive"
TEMPLATE_CACHE = "template_list_cache"
SHOULD_UPDATE_TEMPLATE = "should_update_template"
ISSUE_PJ_USER_RELATION_KEY = "issue_pj_user_relation"


class RedisOperator:
    def __init__(self, redis_base_url):
        self.redis_base_url = redis_base_url
        # prod
        self.pool = redis.ConnectionPool(
            host=self.redis_base_url.split(":")[0],
            port=int(self.redis_base_url.split(":")[1]),
            decode_responses=True,
        )
        self.r = redis.Redis(connection_pool=self.pool)

    #####################
    # String type
    #####################
    def str_get(self, key: str) -> str:
        return self.r.get(key)

    def str_set(self, key: str, value: str) -> bool:
        """
        Returns: The action is successful or not
            True / False
        """
        return self.r.set(key, value)

    def str_delete(self, key) -> bool:
        """
        Returns: The action is successful or not
            True / False
        """
        return self.r.delete(key) == 1

    #####################
    # Boolean type
    #####################
    def bool_get(self, key: str) -> bool:
        """
        Get a boolean value from redis. Redis stores boolean into strings,
        so this function will convert strings below to ``True``.

            - "1"
            - "true"
            - "yes"

        Other values will be converted to ``False``.

        :param key: The key to get
        Returns: The action is successful or not
            True / False
        """
        value: Optional[str] = self.r.get(key)
        if value:  # if value is not None or not empty string
            if value.lower() in ("1", "true", "yes"):
                return True
        return False

    def bool_set(self, key: str, value: bool) -> bool:
        """
        Set a boolean value to redis.

        Args:
            key: The key to set
            value: The boolean value to set

        Returns: True if set successfully, False if not
            True / False
        """
        return self.r.set(key, str(value).lower())

    def bool_delete(self, key: str) -> bool:
        """
        Delete a key from redis.

        Args:
            key: The key to delete

        Returns: True if the key was deleted, False if the key did not exist
            True / False
        """
        result: int = self.r.delete(key)
        if result == 1:
            return True
        else:
            return False

    #####################e
    # Dictionary type
    #####################
    def dict_set_all(self, key: str, value: dict[str, str]) -> bool:
        """
        Returns: The action is successful or not
            True / False
        """
        return self.r.hset(key, mapping=value) == 1

    def dict_set_certain(self, key: str, sub_key: str, value: str) -> bool:
        """
        Returns: The action is successful or not
            True / False
        """
        return self.r.hset(key, sub_key, value) == 1

    def dict_get_all(self, key: str) -> dict[str, str]:
        return self.r.hgetall(key)

    def dict_get_certain(self, key: str, sub_key: Union[str, int]) -> str:
        return self.r.hget(key, sub_key)

    def dict_delete_certain(self, key: str, sub_key: str) -> bool:
        return self.r.hdel(key, sub_key) == 1

    def dict_delete_all(self, key: str) -> str:
        value = self.r.hgetall(key)
        self.r.delete(key)
        return value

    def dict_len(self, key: str) -> int:
        return self.r.hlen(key)


redis_op = RedisOperator(config.REDIS_BASE_URL)


#####################
# Template cache
#####################


def update_template_cache_all(data: dict) -> None:
    """
    Handy function to update all template cache.

    Returns:
        None.
    """
    if data:
        delete_template_cache()
        redis_op.dict_set_all(TEMPLATE_CACHE, data)
        redis_op.bool_set(SHOULD_UPDATE_TEMPLATE, False)


def should_update_template_cache() -> bool:
    """
    Handy function to check if template cache should be updated.

    Returns: Redis value of template cache update flag.
    """
    return redis_op.bool_get(SHOULD_UPDATE_TEMPLATE)


def delete_template_cache() -> None:
    """
    Delete all template cache.

    Returns:
        None
    """
    redis_op.dict_delete_all(TEMPLATE_CACHE)
    redis_op.bool_set(SHOULD_UPDATE_TEMPLATE, True)


def update_template_cache(id, dict_val) -> None:
    """
    Handy function to update certain template cache.

    Returns:
        None.
    """
    redis_op.dict_set_certain(TEMPLATE_CACHE, id, json.dumps(dict_val, default=str))


def get_template_caches_all():
    """
    Handy function to return all template cache.

    Returns: Redis value of all template cache.
    """
    redis_data: dict[str, str] = redis_op.dict_get_all(TEMPLATE_CACHE)
    out: list[dict[str, Any]] = [{_: json.loads(redis_data[_])} for _ in redis_data]
    return out


def count_template_number() -> int:
    """
    Count the number of all templates

    Returns: number of templates
    """
    return redis_op.dict_len(TEMPLATE_CACHE)
