"""
Shared, generic mixins that are not permissions and not models.
"""


class RequestUserContextMixin:
    """
    DRF serializer mixin exposing the current request user via
    self.current_user.
    """

    @property
    def current_user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)