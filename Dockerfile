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


##########################################################################################
# Dockerfile with instructions for building the Docker image of the application.
#
# Docs: https://docs.docker.com/engine/reference/builder/
##########################################################################################

# Dockerfile syntax definition. Required to mount package manager cache directories.
# See Dockerfile syntax tags here: https://hub.docker.com/r/docker/dockerfile
# syntax=docker/dockerfile:1

##########################################################################################
# STAGE 1: COMPILE
##########################################################################################
# Pull official base image.
ARG DOCKER_REGISTRY=docker.io/library
ARG BASE_IMAGE
ARG BASE_TAG

# Not the final image, will appear as `<none>:<none>`.
FROM ${DOCKER_REGISTRY}/${BASE_IMAGE}:${BASE_TAG} AS compile-image

# Adding labels.
LABEL author="Viacheslav Kolupaev"
LABEL stage=compile-image

# Create a temporary folder to hold the files.
WORKDIR /usr/src/app

# Prevents Python from writing pyc files to disk.
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr.
ENV PYTHONUNBUFFERED 1

## Prepare virtualenv.
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

# `pip` configuration befor installing dependencies.
COPY pip.conf pip.conf
ENV PIP_CONFIG_FILE pip.conf

# Install Python dependencies.
COPY ./requirements.txt .
# Docs: https://docs.docker.com/engine/reference/builder/#run---mounttypecache
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip/ \
    pip install --upgrade pip \
    && pip install -r requirements.txt


##########################################################################################
# STAGE 2: BUILD
##########################################################################################
# Pull official base image.
# The final image, will appear as `image_name:image_tag` (`docker build -t` option)
FROM ${DOCKER_REGISTRY}/${BASE_IMAGE}:${BASE_TAG} AS build-image

# Setting the application root folder.
ARG APP_NAME
ENV APP_ROOT="/usr/src/${APP_NAME}"

# Setting the git revision short SHA.
ARG VCS_REF
ENV VCS_REF=${VCS_REF}

# Adding labels.
LABEL author="Viacheslav Kolupaev"
LABEL stage=build-image
LABEL app_name=${APP_NAME}
LABEL vcs_ref=${VCS_REF}

# Prevents Python from writing pyc files to disk.
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr.
ENV PYTHONUNBUFFERED 1

# Create a user group 'app_group'. Create a user 'app_user' under 'app_group'.
RUN addgroup --system app_group \
    && adduser --system --home ${APP_ROOT} --ingroup app_group app_user

# Switch to non-root user.
USER app_user

# Set work directory.
WORKDIR ${APP_ROOT}

ENV VIRTUAL_ENV=/opt/venv

## Copy Python dependencies from build image.
COPY --chown=app_user:app_group --from=compile-image ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Make sure we use the virtualenv:
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

ENV PYTHONPATH ${APP_ROOT}

# Copy project.
COPY --chown=app_user:app_group ./ ${APP_ROOT}

# Chown all the files to the app_user.
RUN chown -R app_user:app_group ${APP_ROOT}

# Server start.
ENTRYPOINT ["/bin/bash", "docker_entrypoint.sh"]
