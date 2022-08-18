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


"""Load testing module using the `locust` library.

The `locust-plugins.Users.RestUser` plugin is used to test REST API endpoints.
"""

import logging
from typing import Any, Final
from uuid import uuid4

import autoviv  # type: ignore[import]
from locust import constant_throughput, env, events, tag, task
from locust_plugins.users import RestResponseContextManager, RestUser
from pydantic import ValidationError
from typeguard import typechecked

from locust_standalone.schemas.common_schemas import ControllerEndpointRequestSchema
from src.locust_standalone.config import config


@events.quitting.add_listener
def _(environment: env.Environment) -> None:
    """Set the exit-code to non-zero.

    Set the exit-code to non-zero if any of the following conditions are met:
        * More than 1% of the requests failed.
        * The average response time is longer than 200 ms.
        * The 95th percentile for response time is larger than 800 ms.

    `quitting` — EventHook. Fired after quitting events, just before process is exited.

    Args:
        environment: `locust` Environment instance.

    """
    max_failure_ratio: Final[int] = 1  # valid values: from 1 to 100.
    max_avg_response_time: Final[int] = 200
    response_time_precent: Final[float] = 0.95
    response_time_precentile_cutoff: Final[int] = 800

    if environment.stats.total.fail_ratio * 100 > max_failure_ratio:
        logging.error('Test failed due to failure ratio > {0}%'.format(max_failure_ratio))
        environment.process_exit_code = 1
    elif environment.stats.total.avg_response_time > max_avg_response_time:
        logging.error('Test failed due to average response time > {0} ms'.format(max_avg_response_time))
        environment.process_exit_code = 1
    elif environment.stats.total.get_response_time_percentile(response_time_precent) > response_time_precentile_cutoff:
        logging.error('Test failed due to {0}th percentile response time > {1} ms'.format(
            int(response_time_precent * 100),
            response_time_precentile_cutoff,
        ),
        )
        environment.process_exit_code = 1
    else:
        environment.process_exit_code = 0


def get_request_payload() -> dict[str, Any]:
    """Get the request payload.

    The raw data is checked against the Pydantic request schema.
    In case of a validation error, further work of the application is interrupted.

    Returns:
        Dictionary with payload data for the request, validated via Pydantic schema

    Raises:
        ValidationError: if the data has not been validated against the Pydantic schema
        TypeError: if the data type is incompatible with the Pydantic schema

    """
    request_payload_raw = {
        'requesting_service_name': 'locust_standalone',
    }

    try:
        request_payload_parsed = ControllerEndpointRequestSchema.parse_obj(request_payload_raw)
    except ValidationError as exc:
        logging.error(
            (
                '{exc_name} occurred while trying to initialize {schema_name}. ' +
                'Found the following errors: {errors}.'
            ).format(
                exc_name=exc.__class__.__name__,
                schema_name=ControllerEndpointRequestSchema.__name__,
                errors=exc.json(),
            ),
        )
        raise exc
    except TypeError as exc:
        logging.error(
            (
                '{exc_name} occurred while trying to initialize {schema_name}. ' +
                'Received the following record argument: {type_of_validated_data}; {validated_data}.'
            ).format(
                exc_name=exc.__class__.__name__,
                schema_name=ControllerEndpointRequestSchema.__name__,
                type_of_validated_data=type(request_payload_raw),
                validated_data=request_payload_raw,
            ),
        )
        raise exc

    return request_payload_parsed.dict()


class FastApiRestUser(RestUser):
    """User to test the REST API powered by FastAPI.

    `RestUser` based on the `FastHttpUser` class.
    Docs: https://docs.locust.io/en/stable/increase-performance.html#fasthttpuser-class

    Uses `locust-plugins`.
    Code example: https://github.com/SvenskaSpel/locust-plugins/blob/master/examples/rest_ex.py

    Order of events: https://github.com/locustio/locust/blob/master/examples/test_data_management.py
    """
    host = str(config.LOCUST_HOST)
    wait_time = constant_throughput(1)

    @typechecked()
    def check_resp_js(self, resp: RestResponseContextManager) -> None:
        """Check that the `resp.js` object exists and does not contain an error message."""
        if not resp.js:
            resp.failure(
                'resp.js is None, which it will be when there is a connection failure, a non-json response etc.',
            )

        if not isinstance(resp.js, autoviv.Dict):
            resp.failure(
                "Invalid 'resp.js' object type. Should be: 'autoviv.Dict'. Received: '{type_of_resp_js}'.".format(
                    type_of_resp_js=type(resp.js),
                ),
            )

        if resp.js and 'error' in resp.js and resp.js['error'] is not None:
            resp.failure(resp.js['error'])

    @typechecked()
    def validate_resp_data(self, resp: RestResponseContextManager) -> None:
        """Validate response data against the Pydantic schema.

        In case of a validation error, the application will not be interrupted.
        `locust` will log the error and reflect in final test statistics.

        Args:
            resp: response received from REST API endpoint

        """
        response_data_raw = resp.js

        try:
            ControllerEndpointRequestSchema.parse_obj(response_data_raw)
        except ValidationError as exc:
            resp.failure(
                (
                    '{exc_name} occurred while trying to initialize {schema_name}. ' +  # noqa: WPS226
                    'Found the following errors: {errors}.'
                ).format(
                    exc_name=exc.__class__.__name__,
                    schema_name=ControllerEndpointRequestSchema.__name__,
                    errors=exc.json(),
                ),
            )
        except TypeError as exc:
            resp.failure(
                (
                    '{exc_name} occurred while trying to initialize {schema_name}. ' +  # noqa: WPS226
                    'Received the following record argument: {type_of_validated_data}; {validated_data}.'
                ).format(
                    exc_name=exc.__class__.__name__,
                    schema_name=ControllerEndpointRequestSchema.__name__,
                    type_of_validated_data=type(response_data_raw),
                    validated_data=response_data_raw,
                ),
            )

    @tag('fast', 'rest_api')
    @task(1)
    def test_performance_some_rest_api_endpoint(self) -> None:
        """Test the performance of some REST API endpoint."""
        request_payload = get_request_payload()
        idempotency_key = uuid4()

        # FastHttpSession class: https://docs.locust.io/en/stable/increase-performance.html#fasthttpsession-class
        with self.rest(
            method='POST',
            url='api/v1/some_rest_api_endpoint',
            data=None,
            json=request_payload,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'idempotency-key': idempotency_key,
            },
            auth=None,
        ) as rest_user_resp:
            self.check_resp_js(resp=rest_user_resp)
            self.validate_resp_data(resp=rest_user_resp)
