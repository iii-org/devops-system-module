import os
from module.request import Request
from typing import Any
from gitlab import Gitlab as IIIGitlab


DEFAULT_REPO = "iiidevops"


class GitLabOperator(Request):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.url = f'{os.getenv("GITLAB_BASE_URL")}api/v4'
        private_token = os.getenv("GITLAB_PRIVATE_TOKEN")

        self.headers = {"Authorization": f"Bearer {private_token}"}
        self.gl = IIIGitlab(
            os.getenv("GITLAB_BASE_URL"),
            private_token=private_token,
            ssl_verify=False,
        )

    ############################
    # Namespace
    ############################
    def gl_get_specific_namespace(self, namespace_name: str) -> dict[str, Any]:
        rets = self.api_get("/namespaces", params={"search": namespace_name}, headers=self.headers).json()
        print(rets)
        for ret in rets:
            if ret["name"] == namespace_name:
                return ret

        return {}

    #####################
    # Project
    #####################
    def gl_get_all_project(self) -> list[dict[str, Any]]:
        return self.gl.projects.list(all=True)

    def gl_get_project_by_name(self, project_name: str) -> dict[str, Any]:
        project_list = self.api_get("/projects", params={"search": project_name}, headers=self.headers).json()

        result = None
        for project in project_list:
            if project.get("name") == project_name and project.get("namespace").get("name") == DEFAULT_REPO:
                result = project
                break
        return result

    def gl_create_project(self, args: dict[str, Any]):
        """
        Args:
            args:
            - *name: project name
            - namespace_id: group of the project
            - *description: project's description
        """
        return self.api_post("/projects", params=args, headers=self.headers).json()

    def create_project(self, kwargs: dict[str, Any]):
        """
        Args:
            kwargs:
            - *name: project name
            - group_name: group of the project
            - *description: project's description
        """
        group_name = kwargs.pop("group_name", DEFAULT_REPO)
        group_info = self.gl_get_specific_namespace(group_name)
        if not group_info:
            return self.gl_create_project({"name": kwargs["name"], "description": kwargs["description"]})
        return self.gl_create_project(
            {"name": kwargs["name"], "description": kwargs["description"], "namespace_id": group_info["id"]}
        )

    def gl_get_project(self, repo_id):
        return self.api_get(f"/projects/{repo_id}", {"statistics": "true"}, headers=self.headers).json()

    def gl_update_project(self, repo_id, description):
        params = {"description": description}
        return self.api_put(f"/projects/{repo_id}", params=params, headers=self.headers)

    def gl_update_project_attributes(self, repo_id, attributes: dict):
        return self.api_put(f"/projects/{repo_id}", params=attributes, headers=self.headers)

    def gl_delete_project(self, repo_id):
        return self.api_delete(f"/projects/{repo_id}", headers=self.headers)
