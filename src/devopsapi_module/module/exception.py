class ModuleException(Exception):
    """ModuleException

    Attributes:
        message: Union[str, dict]
        module: str (module name)

    """

    def __init__(self, module, message="Error occur."):
        self.message = message
        self.module = module

    def __str__(self):
        return f"module: {self.module}, message: {self.message}"


class GitLabException(ModuleException):
    """GitLabException

    Attributes:
        message: str

    """

    def __init__(self, module="Gitlab", message="Gitlab error occur."):
        super().__init__(module=module, message=message)


class RequestException(Exception):
    """RequestException

    Attributes:
        message: str

    """

    def __init__(self, status_code, message="Request error occur."):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return f"status_code: {self.status_code}, message: {self.message}"
