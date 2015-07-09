from .base import *  # noqa

# Automatically import custom settings file for current user, if it exists,
# i.e. if your username is hulken, the file should be named local_hulken.py.
try:
    __import__('local_{0}'.format(os.getlogin()), globals=globals(), level=1)
except ImportError:
    pass
