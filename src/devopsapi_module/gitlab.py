import os
from module.request import Request
from gitlab import Gitlab as IIIGitlab
from module.exception import GitLabException
from module import config

# ======== for typing ========
from typing import Any, Union, Literal
from requests.models import Response


DEFAULT_REPO = "iiidevops"


class GitLabOperator(Request):
    """
    Common parameter variables:
    - repo_id: The ID or URL-encoded path of the project owned by the authenticated user
    - ref: Create tag using commit SHA, another tag name, or branch name


    """

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

    def gl_list_namespace(self) -> dict[str, Any]:
        return self.api_get("/namespaces", headers=self.headers).json()

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
        return self.api_get("/users", params=args, headers=self.headers)

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
        return self.api_post("/users", data=data, headers=self.headers).json()

    def gl_update_password(self, repository_user_id: str, new_pwd: str) -> Response:
        return self.api_put(
            f"/users/{repository_user_id}",
            params={"password": new_pwd, "skip_reconfirmation": True},
            headers=self.headers,
        )

    def gl_update_email(self, repository_user_id: str, new_email: str) -> Response:
        return self.api_put(
            f"/users/{repository_user_id}",
            params={"email": new_email, "skip_reconfirmation": True},
            headers=self.headers,
        )

    def gl_update_user_name(self, repository_user_id: str, new_name: str) -> Response:
        return self.api_put(
            f"/users/{repository_user_id}", params={"name": new_name, "skip_reconfirmation": True}, headers=self.headers
        )

    def gl_update_user_state(self, repository_user_id: str, block_status: bool) -> Response:
        if block_status:
            return self.api_post(f"/users/{repository_user_id}/block", headers=self.headers)
        else:
            return self.api_post(f"/users/{repository_user_id}/unblock", headers=self.headers)

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
        return self.api_get(f"/projects/{repo_id}/members", params=kwargs, headers=self.headers)

    def gl_project_add_member(self, repo_id: str, repository_user_id: str) -> Response:
        params = {
            "user_id": repository_user_id,
            "access_level": 40,
        }
        return self.api_post(f"/projects/{repo_id}/members", params=params, headers=self.headers)

    def gl_project_delete_member(self, repo_id: str, repository_user_id: str) -> Response:
        return self.api_delete(f"/projects/{repo_id}/members/{repository_user_id}", headers=self.headers)

    ############################
    # Variable
    ############################
    def gl_get_all_global_variable(self) -> dict[str, Any]:
        return self.api_get("/admin/ci/variables", headers=self.headers).json()

    def gl_get_global_variable(self, key: str) -> dict[str, Any]:
        return self.api_get(f"/admin/ci/variables/{key}", headers=self.headers).json()

    def gl_create_global_variable(self, data: dict[str, str]) -> dict[str, Any]:
        """
        Args:
            data:
            - key: key of the variable
            - value: content of the variable
            - variable_type: env_var / file
        """
        return self.api_post("/admin/ci/variables", data=data, headers=self.headers).json()

    def gl_update_global_variable(self, key: str, data: dict[str, str]) -> dict[str, Any]:
        """
        Args:
            data:
            - value(str): content of the variable
            - variable_type(str): env_var / file
            - protected(bool):
            - masked(bool):
        """
        return self.api_put(f"/admin/ci/variables/{key}", data=data, headers=self.headers).json()

    def gl_delete_global_variable(self, key: str) -> dict[str, Any]:
        return self.api_delete(f"/admin/ci/variables/{key}", headers=self.headers).json()

    def gl_get_pj_variable(self, repo_id: int) -> dict[str, Any]:
        return self.api_get(f"/projects/{repo_id}/variables", headers=self.headers).json()

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
        return self.api_post(f"/projects/{repo_id}/variables", data=data, headers=self.headers).json

    def gl_delete_pj_variable(self, repo_id: int, key: str) -> dict[str, Any]:
        return self.api_delete(f"/projects/{repo_id}/variables/{key}", headers=self.headers).json

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

        ret = self.api_get(f"/projects/{repo_id}/pipelines", params=params, headers=self.headers)
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
        return self.api_get(f"/projects/{repo_id}/pipelines/{pipeline_id}", headers=self.headers).json()

    def gl_get_pipeline_console(self, repo_id: int, job_id: int) -> str:
        return self.api_get(f"/projects/{repo_id}/jobs/{job_id}/trace", headers=self.headers).content.decode("utf-8")

    def gl_create_pipeline(self, repo_id: int, branch: str) -> dict[str, Any]:
        return self.api_post(f"/projects/{repo_id}/pipeline", {"ref": branch}, headers=self.headers).json()

    def create_pipeline(self, repo_id: int, branch: str) -> dict[str, Any]:
        return self.gl_create_pipeline(repo_id, branch)

    def get_pipeline_jobs_status(self, repo_id: int, pipeline_id: int, with_commit_msg: bool = False) -> dict[str, int]:
        jobs = self.gl_pipeline_jobs(repo_id, pipeline_id)
        total, success = len(jobs), len([job for job in jobs if job["status"] == "success"])

        branch = self.gl_get_single_pipeline(repo_id, pipeline_id)["ref"]
        ret = {"status": {"total": total, "success": success}}
        if with_commit_msg:
            commit_message = jobs[0].get("commit", {}).get("title", "") if jobs else ""
            ret.update({"commit_message": commit_message, "commit_branch": branch})
        return ret

    ############################
    # Pipeline Job
    ############################

    def gl_rerun_pipeline_job(self, repo_id: int, pipeline_id: int) -> dict[str, Any]:
        return self.api_post(f"/projects/{repo_id}/pipelines/{pipeline_id}/retry", headers=self.headers).json()

    def gl_stop_pipeline_job(self, repo_id: int, pipeline_id: int) -> dict[str, Any]:
        return self.api_post(f"/projects/{repo_id}/pipelines/{pipeline_id}/cancel", headers=self.headers).json()

    def gl_pipeline_jobs(self, repo_id: int, pipeline_id: int) -> dict[str, Any]:
        return self.api_get(f"/projects/{repo_id}/pipelines/{pipeline_id}/jobs", headers=self.headers).json()

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
            output = self.api_get(f"/projects/{repo_id}/repository/branches", params=params, headers=self.headers)
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
            headers=self.headers,
        )
        return output.json()

    def gl_get_branch(self, repo_id: str, branch: str) -> dict[str, Any]:
        output = self.api_get(f"/projects/{repo_id}/repository/branches/{branch}", headers=self.headers)
        return output.json()

    def gl_delete_branch(self, repo_id: str, branch: str) -> Response:
        output = self.api_delete(f"/projects/{repo_id}/repository/branches/{branch}", headers=self.headers)
        return output

    def gl_list_protect_branches(self, repo_id: str) -> dict[str, Any]:
        output = self.api_get(f"/projects/{repo_id}/protected_branches", headers=self.headers)
        return output.json()

    def gl_unprotect_branch(self, repo_id: str, branch: str) -> Response:
        output = self.api_delete(f"/projects/{repo_id}/protected_branches/{branch}", headers=self.headers)
        return output

    ############################
    # Commit
    ############################
    def gl_get_commit(self, repo_id: str, commit_id: str) -> dict[str, Any]:
        return self.api_get(f"/projects/{repo_id}/repository/commits/{commit_id}", headers=self.headers).json()

    def gl_get_commits(self, repo_id: str, branch: str, per_page=100, page=1, since=None) -> dict[str, Any]:
        return self.api_get(
            f"/projects/{repo_id}/repository/commits",
            params={
                "ref_name": branch,
                "per_page": per_page,
                "since": since,
                "page": page,
            },
            headers=self.headers,
        ).json()

    def create_commit(self, repo_id: str, branch: str, commit_message: str, actions=[]) -> dict[str, Any]:
        """
        Args:
            actions: [ create , delete , move , update , chmod ]
        """
        return self.api_post(
            f"/projects/{repo_id}/repository/commits",
            data={"branch": branch, "commit_message": commit_message, "actions": actions},
            headers=self.headers,
        ).json()

    def gl_get_commits_by_author(self, repo_id: str, branch: str, author: str = None) -> list[dict]:
        commits = self.gl_get_commits(repo_id, branch)
        if author is None:
            return commits
        output = [commit for commit in commits if commit.get("author_name") != author]
        return output

    def gl_get_commits_by_members(self, repo_id: str, branch: str) -> list[dict[str, Any]]:
        commits = self.gl_get_commits(repo_id, branch)
        output = [
            commit
            for commit in commits
            if (
                commit.get("author_name") != "Administrator"
                and commit.get("committer_name") != "Administrator"
                and not commit.get("author_name", "").startswith("專案管理機器人")
                and not commit.get("committer_name", "").startswith("專案管理機器人")
            )
        ]
        return output

    ############################
    # Tags
    ############################

    def get_tags(
        self,
        repo_id: Union[int, str],
        order_by: str = None,
        sort: str = None,
        search: str = None,
    ) -> dict[str, Any]:
        params = {}
        if order_by:
            params["order_by"] = order_by
        if sort:
            params["sort"] = sort
        if search:
            params["search"] = search

        return self.__api_get(
            f"/projects/{repo_id}/repository/tags",
            params,
            headers=self.headers,
        ).json()

    def is_tag_exist(self, repo_id: Union[int, str], pattern: str) -> bool:
        """
        Args:
            pattern: tag name
        """
        is_exist = False

        for tag in self.get_tags(repo_id, search=pattern):
            if tag.get("name", None) == pattern:
                is_exist = True
                break

        return is_exist

    def create_tag(self, repo_id: Union[int, str], tag_name: str, ref: str, message: str = None) -> dict[str, Any]:
        """
        Args:
            message: Creates annotated tag
        """
        params: dict[str, str] = {}
        if tag_name:
            params["tag_name"] = tag_name
        if ref:
            params["ref"] = ref
        if message:
            params["message"] = message

        return self.__api_post(
            f"/projects/{repo_id}/repository/tags",
            params=params,
            headers=self.headers,
        ).json()

    def delete_tag(self, repo_id: Union[int, str], tag_name: str) -> Response:
        """
        Args:
            repo_id: The ID or URL-encoded path of the project owned by the authenticated user
        """
        return self.__api_delete(
            f"/projects/{repo_id}/repository/tags/{tag_name}",
            headers=self.headers,
        )

    ############################
    # Files
    ############################
    def __gl_file_common_process(self, repo_id: str, args, method) -> dict[str, Any]:
        file_path = f'/projects/{repo_id}/repository/files/{args["file_path"]}'
        params = {
            key: args["key"]
            for key in [
                "branch",
                "start_branch",
                "encoding",
                "author_email",
                "author_name",
                "content",
                "commit_message",
            ]
        }
        method_exec_func_mapping = {"POST": self.api_post, "PUT": self.api_put}
        output = method_exec_func_mapping[method.upper()](file_path, params=params, headers=self.headers).json()
        output = {
            "file_path": output["file_path"],
            "branch_name": output["branch"],
        }
        return output

    def gl_add_file(self, repo_id: str, args) -> dict[str, Any]:
        return self.__gl_file_common_process(repo_id, args, "POST")

    def gl_update_file(self, repo_id: str, args) -> dict[str, Any]:
        return self.__gl_file_common_process(repo_id, args, "PUT")

    def gl_get_file(self, repo_id: str, branch: str, file_path: str) -> dict[str, Any]:
        output = self.__api_get(f"/projects/{repo_id}/repository/files/{file_path}", params={"ref": branch}).json()
        return {
            "file_name": output["file_name"],
            "file_path": output["file_path"],
            "size": output["size"],
            "encoding": output["encoding"],
            "content": output["content"],
            "content_sha256": output["content_sha256"],
            "ref": output["ref"],
            "last_commit_id": output["last_commit_id"],
        }

    def gl_delete_file(self, repo_id: str, file_path: str, args, branch=None) -> Response:
        if branch is None:
            pj = self.gl.projects.get(repo_id)
            branch = pj.default_branch
        return self.__api_delete(
            f"/projects/{repo_id}/repository/files/{file_path}",
            params={
                "branch": branch,
                "author_email": config.AM_EMAIL,
                "author_name": config.AM_ACCOUNT,
                "commit_message": args["commit_message"],
            },
        )

    ############################
    # Releases
    ############################
    def gl_get_release(self, repo_id: str, tag_name: str) -> dict[str, Any]:
        return self.__api_get(f"/projects/{repo_id}/releases/{tag_name}").json()

    def gl_create_release(self, repo_id: str, data) -> dict[str, Any]:
        return self.__api_post(f"/projects/{repo_id}/releases", params=data).json()

    def gl_delete_release(self, repo_id: str, tag_name: str) -> Response:
        return self.__api_delete(f"/projects/{repo_id}/releases/{tag_name}")


# gl_get_network
