import os
from module.request import Request
from typing import Any
from gitlab import Gitlab as IIIGitlab
from module.exception import GitLabException

# ======== for typing ========
from requests.models import Response


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

    def gl_create_project(self, args: dict[str, Any]) -> Response:
        """
        Args:
            args:
            - *name: project name
            - namespace_id: group of the project
            - *description: project's description
        """
        return self.api_post("/projects", params=args, headers=self.headers).json()

    def create_project(self, kwargs: dict[str, Any]) -> dict[str, Any]:
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

    def gl_get_project(self, repo_id: str) -> Response:
        return self.api_get(f"/projects/{repo_id}", {"statistics": "true"}, headers=self.headers).json()

    def gl_update_project(self, repo_id: str, description: str) -> Response:
        params = {"description": description}
        return self.api_put(f"/projects/{repo_id}", params=params, headers=self.headers)

    def gl_update_project_attributes(self, repo_id: str, attributes: dict[str, Any]) -> Response:
        return self.api_put(f"/projects/{repo_id}", params=attributes, headers=self.headers)

    def gl_delete_project(self, repo_id: str) -> Response:
        return self.api_delete(f"/projects/{repo_id}", headers=self.headers)

    #####################
    # User
    #####################
    def gl_get_user_list(self, args) -> Response:
        """
        Args:
            kwargs:
            - username: Get a single user with a specific username.
            - search: Search for a name, username, or public email
            - active: Filters only active users. Default is false.
            - blocked: Filters only blocked users. Default is false.
        """
        return self.api_get("/users", params=args)

    def gl_create_user(self, args, user_source_password: str, is_admin: bool = False) -> Response:
        """
        Args:
            kwargs:
            - admin: User is an administrator.
            - *name: Name of the user.
            - *username: Login account of the user.
            - *email
            - password
            - skip_confirmation: Do not need to confirm, False by default.
        """
        data = {
            "name": args["name"],
            "email": args["email"],
            "username": args["login"],
            "password": user_source_password,
            "skip_confirmation": True,
        }
        if is_admin:
            data["admin"] = True
        return self.api_post("/users", data=data).json()

    def gl_update_password(self, repository_user_id: str, new_pwd: str) -> Response:
        return self.api_put(
            f"/users/{repository_user_id}",
            params={"password": new_pwd, "skip_reconfirmation": True},
        )

    def gl_update_email(self, repository_user_id: str, new_email: str) -> Response:
        return self.api_put(
            f"/users/{repository_user_id}",
            params={"email": new_email, "skip_reconfirmation": True},
        )

    def gl_update_user_name(self, repository_user_id: str, new_name: str) -> Response:
        return self.api_put(
            f"/users/{repository_user_id}",
            params={"name": new_name, "skip_reconfirmation": True},
        )

    def gl_update_user_state(self, repository_user_id: str, block_status: bool) -> Response:
        if block_status:
            return self.api_post(f"/users/{repository_user_id}/block")
        else:
            return self.api_post(f"/users/{repository_user_id}/unblock")

    def gl_delete_user(self, repository_user_id: str) -> Response:
        return self.api_delete(f"/users/{repository_user_id}")

    #####################
    # Project's members
    #####################
    def gl_project_list_member(self, repo_id: str, kwargs: dict[str, Any] = {}) -> Response:
        """
        Args:
            kwargs:
            - page(int)
            - per_page(int)
            - query(string): Search for a specific members
        """
        return self.api_get(f"/projects/{repo_id}/members", params=kwargs)

    def gl_project_add_member(self, repo_id: str, repository_user_id: str) -> Response:
        params = {
            "user_id": repository_user_id,
            "access_level": 40,
        }
        return self.api_post(f"/projects/{repo_id}/members", params=params)

    def gl_project_delete_member(self, repo_id: str, repository_user_id: str) -> Response:
        return self.api_delete(f"/projects/{repo_id}/members/{repository_user_id}")

    ############################
    # Variable
    ############################
    def gl_get_all_global_variable(self) -> dict[str, Any]:
        return self.api_get("/admin/ci/variables").json()

    def gl_get_global_variable(self, key: str) -> dict[str, Any]:
        return self.api_get(f"/admin/ci/variables/{key}").json()

    def gl_create_global_variable(self, data: dict[str, str]) -> dict[str, Any]:
        """
        Args:
            data:
            - key: key of the variable
            - value: content of the variable
            - variable_type: env_var / file
        """
        return self.api_post("/admin/ci/variables", data=data).json()

    def gl_update_global_variable(self, key: str, data: dict[str, str]) -> dict[str, Any]:
        """
        Args:
            data:
            - value(str): content of the variable
            - variable_type(str): env_var / file
            - protected(bool):
            - masked(bool):
        """
        return self.api_put(f"/admin/ci/variables/{key}", data=data).json()

    def gl_delete_global_variable(self, key: str) -> dict[str, Any]:
        return self.api_delete(f"/admin/ci/variables/{key}").json()

    def gl_get_pj_variable(self, repo_id: int) -> dict[str, Any]:
        return self.api_get(f"/projects/{repo_id}/variables").json()

    def gl_create_pj_variable(self, repo_id: int, data: dict[str, str]) -> dict[str, Any]:
        """
        Args:
            data:
            - key(str): key of the variable
            - value(str): content of the variable
            - variable_type(str): env_var / file
            - protected(bool): only export variable on protected branch
            - masked(bool): value will be masked in job logs
            - raw: treated special character as the start of a reference to another variable
        """
        return self.api_post(f"/projects/{repo_id}/variables", data=data).json

    def gl_delete_pj_variable(self, repo_id: int, key: str) -> dict[str, Any]:
        return self.api_delete(f"/projects/{repo_id}/variables/{key}").json

    def create_pj_variable(self, repo_id: int, key: str, value: str, attribute: dict[str, Any] = {}) -> dict[str, Any]:
        data = {"variable_type": "env_var", "protected": False, "masked": True, "raw": True}
        data |= attribute
        data.update({"key": key, "value": value})
        return self.gl_create_pj_variable(repo_id, data)

    ############################
    # Pipeline
    ############################
    def gl_list_pipelines(
        self,
        repo_id: int,
        limit: int,
        start: int,
        branch: str = None,
        sort: str = "desc",
        with_pagination: bool = False,
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:
        page = (start // limit) + 1
        params = {"page": page, "per_page": limit, "sort": sort}
        if branch is not None:
            params["ref"] = branch

        ret = self.api_get(f"/projects/{repo_id}/pipelines", params=params)
        results = ret.json()
        if not with_pagination:
            return results

        headers = ret.headers
        pagination = {
            "total": int(headers.get("X-Total") or 0),
            "current": int(headers.get("X-Page") or 0),
            "prev": int(headers.get("X-Prev-Page") or 0),
            "next": int(headers.get("X-Next-Page") or 0),
            "pages": int(headers.get("X-Total-Pages") or 0),
            "per_page": limit,
        }
        return results, pagination

    def gl_get_single_pipeline(self, repo_id: int, pipeline_id: int) -> dict[str, Any]:
        return self.api_get(f"/projects/{repo_id}/pipelines/{pipeline_id}").json()

    def gl_get_pipeline_console(self, repo_id: int, job_id: int) -> str:
        return self.api_get(f"/projects/{repo_id}/jobs/{job_id}/trace").content.decode("utf-8")

    def gl_create_pipeline(self, repo_id: int, branch: str) -> dict[str, Any]:
        return self.api_post(f"/projects/{repo_id}/pipeline", {"ref": branch}).json()

    def create_pipeline(self, repo_id: int, branch: str) -> dict[str, Any]:
        return self.gl_create_pipeline(repo_id, branch)

    ############################
    # Namespace
    ############################
    def gl_list_namespace(self) -> dict[str, Any]:
        return self.api_get("/namespaces").json()

    def gl_get_specific_namespace(self, namespace_name: str) -> dict[str, Any]:
        rets = self.api_get("/namespaces", params={"search": namespace_name}).json()
        for ret in rets:
            if ret["name"] == namespace_name:
                return ret

        return {}

    ############################
    # Pipeline Job
    ############################

    def gl_rerun_pipeline_job(self, repo_id: int, pipeline_id: int) -> dict[str, Any]:
        return self.api_post(f"/projects/{repo_id}/pipelines/{pipeline_id}/retry").json()

    def gl_stop_pipeline_job(self, repo_id: int, pipeline_id: int) -> dict[str, Any]:
        return self.api_post(f"/projects/{repo_id}/pipelines/{pipeline_id}/cancel").json()

    def gl_pipeline_jobs(self, repo_id: int, pipeline_id: int) -> dict[str, Any]:
        return self.api_get(f"/projects/{repo_id}/pipelines/{pipeline_id}/jobs").json()

    def rerun_pipeline_job(self, repo_id: int, pipeline_id: int) -> dict[str, Any]:
        pipeline_info = self.gl_get_single_pipeline(repo_id, pipeline_id)
        sha, branch = pipeline_info["sha"], pipeline_info["ref"]
        commit_msg = self.single_commit(repo_id, sha)["title"]
        return self.create_commit(repo_id, branch, commit_msg)

    ############################
    # Branch
    ############################

    def gl_get_branches(self, repo_id: str) -> list[dict[str, Any]]:
        gl_total_branch_list = []
        total_pages = 1
        i = 1
        while i <= total_pages:
            params = {"per_page": 25, "page": i}
            output = self.api_get(f"/projects/{repo_id}/repository/branches", params=params)
            if output.status_code != 200:
                raise GitLabException(message=f"Error while getting git branches, message: {output.json}")
            gl_total_branch_list.extend(output.json())
            total_pages = int(output.headers.get("x-total-pages", total_pages))
            i += 1

        return gl_total_branch_list

    def gl_create_branch(self, repo_id: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        """
        Args:
            kwargs:
            - *branch: Name of the branch.
            - *ref: Branch name or commit SHA to create branch from.
        """
        output = self.api_post(
            f"/projects/{repo_id}/repository/branches",
            params={"branch": kwargs["branch"], "ref": kwargs["ref"]},
        )
        return output.json()

    def gl_get_branch(self, repo_id: str, branch: str) -> dict[str, Any]:
        output = self.api_get(f"/projects/{repo_id}/repository/branches/{branch}")
        return output.json()

    def gl_delete_branch(self, repo_id: str, branch: str) -> Response:
        output = self.api_delete(f"/projects/{repo_id}/repository/branches/{branch}")
        return output

    def gl_list_protect_branches(self, repo_id: str) -> dict[str, Any]:
        output = self.api_get(f"/projects/{repo_id}/protected_branches")
        return output.json()

    def gl_unprotect_branch(self, repo_id: str, branch: str) -> Response:
        output = self.api_delete(f"/projects/{repo_id}/protected_branches/{branch}")
        return output

    ############################
    # Commit
    ############################

    def gl_get_commits(self, repo_id: str, branch: str, per_page=100, page=1, since=None) -> dict[str, Any]:
        return self.api_get(
            f"/projects/{repo_id}/repository/commits",
            params={
                "ref_name": branch,
                "per_page": per_page,
                "since": since,
                "page": page,
            },
        ).json()

    def create_commit(self, repo_id: str, branch: str, commit_message: str, actions=[]) -> dict[str, Any]:
        """
        Args:
            actions: [ create , delete , move , update , chmod ]
        """
        return self.api_post(
            f"/projects/{repo_id}/repository/commits",
            data={"branch": branch, "commit_message": commit_message, "actions": actions},
        ).json()

    def gl_get_commits_by_author(self, repo_id: str, branch: str, author: str = None) -> list[dict]:
        commits = self.gl_get_commits(repo_id, branch)
        if author is None:
            return commits
        output = []
        for commit in commits:
            if commit.get("author_name") != author:
                output.append(commit)
        return output

    def gl_get_commits_by_members(self, repo_id: str, branch: str) -> list[dict[str, Any]]:
        commits = self.gl_get_commits(repo_id, branch)
        output = []
        for commit in commits:
            if (
                commit.get("author_name") != "Administrator"
                and commit.get("committer_name") != "Administrator"
                and not commit.get("author_name", "").startswith("專案管理機器人")
                and not commit.get("committer_name", "").startswith("專案管理機器人")
            ):
                output.append(commit)
        return output
