import os
from environs import Env

__all__ = ("env", )

env = Env()
env.read_env(os.environ.get("CONFIG_FILE", ".env"), recurse=False)
