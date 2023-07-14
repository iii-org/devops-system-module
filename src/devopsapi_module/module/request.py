import requests
import json


# ======== for typing ========
from typing import Any
from requests.models import Response


class Request:
    def __get_request_func(self, method: str) -> callable:
        method = method.upper()

        method_req_func_mapping = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "PATCH": requests.patch,
            "DELETE": requests.delete,
        }
        return method_req_func_mapping[method]

    def api_request(
        self,
        method: str,
        path: str,
        headers: dict[str, Any] = {},
        params: dict[str, Any] = {},
        data: dict[str, Any] = {},
    ) -> Response:
        url, req_func = f"{self.url}{path}", self.__get_request_func(method)

        if data:
            data = json.dumps(data)
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"

        req_func_kwargs = {
            "url": url,
            "headers": headers,
            "params": params,
            "data": data,
            "verify": False,
        }
        return req_func(**req_func_kwargs)

    def api_get(
        self,
        path: str,
        headers: dict[str, Any] = {},
        params: dict[str, Any] = {},
    ) -> Response:
        return self.api_request(
            "GET",
            path,
            headers=headers,
            params=params,
        )

    def api_post(
        self,
        path: str,
        params: dict[str, Any] = {},
        headers: dict[str, Any] = {},
        data: dict[str, Any] = {},
    ) -> Response:
        data = json.dumps(data)
        return self.api_request(
            "POST",
            path,
            headers=headers,
            data=data,
            params=params,
        )

    def api_put(
        self,
        path: str,
        params: dict[str, Any] = {},
        headers: dict[str, Any] = {},
        data: dict[str, Any] = {},
    ) -> Response:
        return self.api_request(
            "PUT",
            path,
            headers=headers,
            data=data,
            params=params,
        )

    def api_patch(
        self,
        path: str,
        headers: dict[str, Any] = {},
        data: dict[str, Any] = {},
    ) -> Response:
        return self.api_request(
            "PATCH",
            path,
            headers=headers,
            data=data,
        )

    def api_delete(
        self,
        path: str,
        headers: dict[str, Any] = {},
        data: dict[str, Any] = {},
    ) -> Response:
        return self.api_request(
            "DELETE",
            path,
            headers=headers,
            data=data,
        )
