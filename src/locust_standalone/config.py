# ########################################################################################
#  Copyright 2022 Viacheslav Kolupaev; author's website address:
#
#      https://vkolupaev.com/?utm_source=c&utm_medium=link&utm_campaign=locust_standalone
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ########################################################################################

"""Application config.

Features of the module:
  1. Read configs from `.env` files and shell environment at the same time.
  2. Keep `development`, `staging` and `production` configs separate.
  3. Convert variable types automatically in the appropriate cases,
     e.g. string to integer conversion.

Use the `AppInternalLogicConfig` class to parameterize the application's internal logic.
Getting access to configs from Python code:

```python
from config import config
print(config.RANDOM_SEED)
```

Changing the `GlobalConfig`, `DevelopmentConfig`, `StagingConfig` and `ProductionConfig`
classes must be done in conjunction with DevOps engineers responsible for the CI/CD of
our team and this project in particular: `Bitbucket`, `Jenkins`, `GitLab`, etc.

The module was developed using [Pydantic Settings management](
https://pydantic-docs.helpmanual.io/usage/settings/).
"""

from pathlib import Path
from typing import Literal, Optional, Union

import pydantic

from locust_standalone.schemas import config_schemas


def _get_path_to_dotenv_file(dotenv_filename: str, num_of_parent_dirs_up: int) -> Optional[Path]:
    """Get the path to the `.env` file.

    This is a helper function.
    The path is calculated relative to the location of this module.

    Args:
        dotenv_filename: the name of the dotenv file, such as `.env`.
        num_of_parent_dirs_up: the number of levels in the hierarchy up to the directory with the dotenv file.

    Returns:
        The `Path` object, if the dotenv file exists. Otherwise, `None`.
    """
    path_to_dotenv_file = Path(__file__).resolve().parents[num_of_parent_dirs_up].joinpath(dotenv_filename)

    if path_to_dotenv_file.exists():
        return path_to_dotenv_file
    return None


class AppInternalLogicConfig(pydantic.BaseModel):
    """Application internal logic config.

    Use this class to parameterize application logic.
    """

    RANDOM_SEED: int = 42


class GlobalConfig(pydantic.BaseSettings, AppInternalLogicConfig):
    """Global configurations.

    `GlobalConfig` defines the variables that propagate through other environment classes
    and the attributes of this class are globally accessible from all other environments.

    In this class, the variables are loaded from the `.env` file. However, if there is a
    shell environment variable having the same name, that will take precedence.

    The class `GlobalConfig` inherits from Pydantic’s `BaseSettings` which helps to load
    and read the variables from the `.env file`. The `.env` file itself is loaded in
    the nested `Config` class.

    Although the environment variables are loaded from the `.env` file, Pydantic also
    loads your actual shell environment variables at the same time.

    From Pydantic’s [documentation](https://pydantic-docs.helpmanual.io/usage/settings/):

    ```text
    Even when using a `.env` file, `pydantic` will still read environment variables
    as well as the `.env` file, environment variables will always take priority over
    values loaded from a dotenv file.
    ```
    """

    # General application config.
    _DEFAULT_APP_NAME_VALUE: str = 'locust_standalone'

    APP_NAME: str = pydantic.Field(
        title='APP_NAME',
        description='The name of the application',
        default=_DEFAULT_APP_NAME_VALUE,
        const=True,
        min_length=1,
    )
    APP_ENV_STATE: config_schemas.EnvState = pydantic.Field(
        env='APP_ENV_STATE',
        default=config_schemas.EnvState.development,
        min_length=1,
    )

    # `locust` config.
    LOCUST_HOST: pydantic.HttpUrl = pydantic.Field(default='http://127.0.0.1:50000')
    LOCUST_USERS: pydantic.PositiveInt = 10
    LOCUST_SPAWN_RATE: pydantic.PositiveInt = 5
    LOCUST_RUN_TIME: str = pydantic.Field(default='30s', min_length=2)
    LOCUST_TAGS: list[str] = pydantic.Field(default=["rest_api","fast"])
    LOCUST_HEADLESS: bool = True
    LOCUST_PRINT_STATS: bool = True
    LOCUST_ONLY_SUMMARY: bool = True
    LOCUST_LOGLEVEL: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = pydantic.Field(default='INFO')

    class Config(object):
        """Pydantic Model Config.

        Loads the dotenv file. Environment variables will always take priority over values
        loaded from a dotenv file.
        """
        env_file: Optional[Path] = _get_path_to_dotenv_file(dotenv_filename='.env', num_of_parent_dirs_up=2)
        anystr_strip_whitespace = True


class DevelopmentConfig(GlobalConfig):
    """Development configurations.

    `DevelopmentConfig` class inherits from the `GlobalConfig` class, and it can define
    additional variables specific to the development environment. It inherits all the
    variables defined in the `GlobalConfig` class.
    """

    # Define here new attributes that are not in the `GlobalConfig` class.

    class Config(object):
        """Pydantic Model Config."""

        anystr_strip_whitespace = True


class StagingConfig(GlobalConfig):
    """Staging configurations.

    `StagingConfig` class also inherits from the `GlobalConfig` class, and it can define
    additional variables specific to the staging environment. It inherits all the
    variables defined in the `GlobalConfig class`.
    """

    # Define here new attributes that are not in the `GlobalConfig` class.

    class Config(object):
        """Pydantic Model Config."""

        anystr_strip_whitespace = True


class ProductionConfig(GlobalConfig):
    """Production configurations.

    `ProductionConfig` class also inherits from the `GlobalConfig` class, and it can
    define additional variables specific to the production environment. It inherits all
    the variables defined in the `GlobalConfig class`.
    """

    # Define here new attributes that are not in the `GlobalConfig` class.

    class Config(object):
        """Pydantic Model Config."""

        anystr_strip_whitespace = True


class FactoryConfig(object):
    """Returns a config instance.

    `FactoryConfig` is the controller class that dictates which config class should be
    activated based on the environment state defined as `APP_ENV_STATE` in the `.env` file.

    If it finds `GlobalConfig().APP_ENV_STATE="development"` then the control flow
    statements in the `FactoryConfig` class will activate the development configs —
    `DevelopmentConfig`.
    """

    def __init__(self, app_env_state: config_schemas.EnvState) -> None:
        """Customize the class instance immediately after its creation."""
        self.app_env_state = app_env_state

    def __call__(self) -> Union[StagingConfig, ProductionConfig, DevelopmentConfig]:
        """Get the application config depending on the environment."""
        if self.app_env_state == config_schemas.EnvState.staging:
            return StagingConfig()
        elif self.app_env_state == config_schemas.EnvState.production:
            return ProductionConfig()
        elif self.app_env_state == config_schemas.EnvState.development:
            return DevelopmentConfig()
        raise ValueError(
            "Incorrect environment variable 'APP_ENV_STATE': {app_env_state}.".format(
                app_env_state=self.app_env_state,
            ),
        )


config = FactoryConfig(app_env_state=GlobalConfig().APP_ENV_STATE)()
