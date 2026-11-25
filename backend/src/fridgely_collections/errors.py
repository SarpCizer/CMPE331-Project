class CollectionError(Exception):
    """A public, deliberately non-sensitive feature error."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def not_found() -> CollectionError:
    # The same response for absent objects and another account's objects.
    return CollectionError(404, "Resource not found")
