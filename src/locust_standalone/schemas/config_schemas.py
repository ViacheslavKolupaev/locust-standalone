# ########################################################################################
#  Copyright (c) 2022. Viacheslav Kolupaev, https://vkolupaev.com/
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may not use this
#  file except in compliance with the License. You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied. See the License for the specific language governing
#  permissions and limitations under the License.
# ########################################################################################


"""Pydantic models of application config fields that are used in other modules.

Placing models in this separate module avoids circular import errors.
"""

import pydantic


class AppVcsRefSchema(pydantic.BaseModel):
    """The current Git commit hash (vcs revision) of the application.

    Use it to save along with the API response.

    An analogue of the `git rev-parse HEAD` command. It is defined externally through the
    corresponding Environment Variable.
    """

    APP_VCS_REF: str = pydantic.Field(
        default=pydantic.Required,
        title='app_vcs_ref',
        alias='app_vcs_ref',
        env='APP_VCS_REF',
        min_length=1,
        example='',
        description=(
            'The current Git commit hash (vcs revision) of the application.<br><br>' +
            'Use it to save along with the API response.<br><br>' +
            'An analogue of the `git rev-parse HEAD` command. It is defined externally' +
            'through the corresponding Environment Variable.'
        ),
    )  # git commit hash
