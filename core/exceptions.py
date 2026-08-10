class UkoreHubError(Exception):
    pass


class ValidationError(UkoreHubError):
    pass


class NotFoundError(UkoreHubError):
    pass


class ConflictError(UkoreHubError):
    """Raised when a shared cloud-synced store (core/vcs/cloud_sync.py)
    detects that another machine wrote a newer version of the same blob
    first."""

    pass


class GitOperationError(UkoreHubError):
    pass


class GitHubAuthError(UkoreHubError):
    pass
