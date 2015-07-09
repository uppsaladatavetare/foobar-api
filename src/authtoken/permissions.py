from rest_framework import permissions


class HasTokenScope(permissions.BasePermission):
    def __init__(self, scope):
        self.scope = scope

    def __call__(self):
        """
        Django Rest Framework expects us to pass a permission class,
        not an instance, and then it will initiate the class on its own.
        We require however that the class is initiated with a token scope name.
        Thanks to this method, we can simply create an instance and when
        DRF will try to initialize it, it will get the already initiated
        instance.
        """
        return self

    def has_permission(self, request, view):
        if request.auth is None:
            return False
        return getattr(request.auth.scopes, self.scope)
