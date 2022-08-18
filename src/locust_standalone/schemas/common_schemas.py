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


"""Commonly used Pydantic data application models."""

import pydantic

# ########################################################################################
# Schemas of common required and optional fields.
# ########################################################################################


class RequestingServiceNameMan(pydantic.BaseModel):
    """The name of the requesting service.

    Required field.
    """
    requesting_service_name: str = pydantic.Field(
        title='requesting_service_name',
        example='the-name-of-the-requesting-service',
        description=(
            'The name of the service requesting the REST API endpoint. ' +
            'Used to log events and collect usage statistics.'
        ),
        min_length=1,
        max_length=45,
    )

    class Config(object):
        """Pydantic Model Config."""

        anystr_strip_whitespace = True


# ########################################################################################
# Schemas of requests and responses.
# ########################################################################################
class ControllerEndpointRequestSchema(
    RequestingServiceNameMan,
):
    """The data schema of the request to the endpoint of the REST API controller."""
    pass
