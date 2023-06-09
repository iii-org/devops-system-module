import json
from datetime import datetime
from typing import Any, Optional, Union
import os
import redis


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
        :return: The action is successful or not
            True / False
        """
        return self.r.set(key, value)

    def str_delete(self, key) -> bool:
        """
        :return: The action is successful or not
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
        :return: The result from redis server
        """
        value: Optional[str] = self.r.get(key)
        if value:  # if value is not None or not empty string
            if value.lower() in ("1", "true", "yes"):
                return True
        return False

    def bool_set(self, key: str, value: bool) -> bool:
        """
        Set a boolean value to redis.

        :param key: The key to set
        :param value: The boolean value to set
        :return: True if set successfully, False if not
        """
        return self.r.set(key, str(value).lower())

    def bool_delete(self, key: str) -> bool:
        """
        Delete a key from redis.

        :param key: The key to delete
        :return: True if the key was deleted, False if the key did not exist
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
        :return: The action is successful or not
            True / False
        """
        return self.r.hset(key, mapping=value) == 1

    def dict_set_certain(self, key: str, sub_key: str, value: str) -> bool:
        """
        :return: The action is successful or not
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


redis_op = RedisOperator(os.getenv("REDIS_BASE_URL"))


#####################
# Template cache
#####################


def update_template_cache_all(data: dict) -> None:
    """
    Handy function to update all template cache.

    :return: None.
    """
    if data:
        delete_template_cache()
        redis_op.dict_set_all(TEMPLATE_CACHE, data)
        redis_op.bool_set(SHOULD_UPDATE_TEMPLATE, False)


def should_update_template_cache() -> bool:
    """
    Handy function to check if template cache should be updated.

    :return: Redis value of template cache update flag.
    """
    return redis_op.bool_get(SHOULD_UPDATE_TEMPLATE)


def delete_template_cache() -> None:
    """
    Delete all template cache.

    :return: None
    """
    redis_op.dict_delete_all(TEMPLATE_CACHE)
    redis_op.bool_set(SHOULD_UPDATE_TEMPLATE, True)


def update_template_cache(id, dict_val) -> None:
    """
    Handy function to update certain template cache.

    :return: None.
    """
    redis_op.dict_set_certain(TEMPLATE_CACHE, id, json.dumps(dict_val, default=str))


def get_template_caches_all():
    """
    Handy function to return all template cache.

    :return: Redis value of all template cache.
    """
    redis_data: dict[str, str] = redis_op.dict_get_all(TEMPLATE_CACHE)
    out: list[dict[str, Any]] = [{_: json.loads(redis_data[_])} for _ in redis_data]
    return out


def count_template_number() -> int:
    """
    Count the number of all templates

    :return: number of templates
    """
    return redis_op.dict_len(TEMPLATE_CACHE)


'''
#####################
#  Server Alive
#####################
"""
Due to redis can only store in string type, 
- 'True' : Server is alive
- 'False': Server is not alive
"""

def get_server_alive() -> bool:
    status = redis_op.str_get(SERVER_ALIVE_KEY)
    return status == "True" if status is not None else status


def update_server_alive(alive) -> bool:
    return redis_op.str_set(SERVER_ALIVE_KEY, alive)


#####################
# Issue Family Cache
#####################

def get_all_issue_relations():
    return redis_op.dict_get_all(ISSUE_FAMILIES_KEY)


# def check_issue_has_son(issue_id: int, by_user_permission: bool = False) -> bool:
#     issue_has_son = redis_op.r.hexists(ISSUE_FAMILIES_KEY, issue_id)
#     if not issue_has_son or not by_user_permission:
#         return issue_has_son

#     son_issue_ids = redis_op.dict_get_certain(ISSUE_FAMILIES_KEY, issue_id)
#     has_issue_per_bools = []
#     for son_issue_id in son_issue_ids.split(","):
#         has_issue_per_bools.append(check_user_has_permission_to_see_issue(son_issue_id))

#     return any(has_issue_per_bools)


def update_issue_relations(issue_families):
    if issue_families != {}:
        redis_op.dict_delete_all(ISSUE_FAMILIES_KEY)
        return redis_op.dict_set_all(ISSUE_FAMILIES_KEY, issue_families)


def update_issue_relation(parent_issue_id, son_issue_ids):
    return redis_op.dict_set_certain(ISSUE_FAMILIES_KEY, parent_issue_id, son_issue_ids)


def remove_issue_relation(parent_issue_id, son_issue_id):
    son_issue_ids = redis_op.dict_get_certain(ISSUE_FAMILIES_KEY, parent_issue_id)
    if son_issue_ids is None:
        return
    son_issue_ids = son_issue_ids.split(",")
    if son_issue_id in son_issue_ids:
        if len(son_issue_ids) == 1:
            redis_op.dict_delete_certain(ISSUE_FAMILIES_KEY, parent_issue_id)
        else:
            son_issue_ids.remove(son_issue_id)
            update_issue_relation(parent_issue_id, ",".join(son_issue_ids))


def remove_issue_relations(parent_issue_id):
    redis_op.dict_delete_certain(ISSUE_FAMILIES_KEY, parent_issue_id)


# def add_issue_relation(parent_issue_id, son_issue_id):
#     if not check_issue_has_son(parent_issue_id):
#         redis_op.dict_set_certain(ISSUE_FAMILIES_KEY, parent_issue_id, str(son_issue_id))
#     else:
#         son_issue_ids = redis_op.dict_get_certain(ISSUE_FAMILIES_KEY, parent_issue_id)
#         son_issue_ids = son_issue_ids.split(",")
#         if son_issue_id not in son_issue_ids:
#             update_issue_relation(parent_issue_id, ",".join(son_issue_ids + [str(son_issue_id)]))


#####################
# Project issue calculate Cache
#####################

def get_certain_pj_issue_calc(pj_id):
    cal_info = redis_op.dict_get_certain(PROJECT_ISSUE_CALCULATE_KEY, pj_id)
    if cal_info is None:
        return {
            "closed_count": 0,
            "overdue_count": 0,
            "total_count": 0,
            "project_status": "not_started",
            "updated_time": datetime.utcnow().isoformat(),
        }
    cal_info_dict = json.loads(cal_info)
    if "T" not in cal_info_dict["updated_time"]:
        cal_info_dict["updated_time"] = (
            datetime.strptime(cal_info_dict["updated_time"], "%Y-%m-%d %H:%M:%S").isoformat()
            if cal_info_dict["updated_time"] not in ["", None]
            else datetime.utcnow().isoformat()
        )
    return cal_info_dict


def update_pj_issue_calcs(project_issue_calculation):
    return redis_op.dict_set_all(PROJECT_ISSUE_CALCULATE_KEY, project_issue_calculation)


def update_pj_issue_calc(pj_id, total_count=0, closed_count=0):
    pj_issue_calc = get_certain_pj_issue_calc(pj_id)
    pj_issue_calc["total_count"] += int(total_count)
    pj_issue_calc["closed_count"] += int(closed_count)

    if pj_issue_calc["total_count"] == 0:
        pj_issue_calc["project_status"] = "not_started"
    elif pj_issue_calc["total_count"] == pj_issue_calc["closed_count"]:
        pj_issue_calc["project_status"] = "closed"
    else:
        pj_issue_calc["project_status"] = "in_progress"

    return redis_op.dict_set_certain(PROJECT_ISSUE_CALCULATE_KEY, pj_id, json.dumps(pj_issue_calc))


#####################
# Issue project user relation Cache
#####################
"""
Don't need this redis table when we remove redmine.
"""

# def get_single_issue_pj_user_relation(issue_id: int) -> dict[int, Any]:
#     redis_data = redis_op.dict_get_certain(ISSUE_PJ_USER_RELATION_KEY, issue_id)
#     if not redis_data:
#         return {}
#     out = json.loads(redis_data)

    # pj_obj = model.Project.query.filter_by(id=out["project_id"]).first()
    # if pj_obj is not None:
    #     out["project_users"] = [str(user["id"]) for user in pj_obj.users]
    # return out


def update_issue_pj_user_relation(issue_id: int, issue_pj_user_relation: dict[str, Any]) -> None:
    return redis_op.dict_set_certain(ISSUE_PJ_USER_RELATION_KEY, issue_id, issue_pj_user_relation)


def update_issue_pj_user_relations(issue_pj_user_relations: dict[int, Any]) -> None:
    if issue_pj_user_relations != {}:
        remove_issue_pj_user_relations()
        redis_op.dict_set_all(ISSUE_PJ_USER_RELATION_KEY, issue_pj_user_relations)


def remove_issue_pj_user_relations() -> None:
    redis_op.dict_delete_all(ISSUE_PJ_USER_RELATION_KEY)


# def check_user_has_permission_to_see_issue(issue_id: int, user_id: str) -> bool:
#     pj_users = get_single_issue_pj_user_relation(int(issue_id)).get("project_users", "")
#     return user_id in pj_users


'''
