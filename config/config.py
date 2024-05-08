import os

from .default import config as default_config
from .development import config as dev_config
from .env import config as envs
from .production import config as prod_config

environment = os.environ["PYTHON_ENV"] or "development"
environment_config = None
if environment == "development":
    environment_config = dev_config
elif environment == "production":
    environment_config = prod_config
else:
    environment_config = {}


CONFIG = {**default_config, **environment_config, **envs}
