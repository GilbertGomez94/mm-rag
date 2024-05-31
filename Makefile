TAG := $(shell TZ=UTC date "+%d%m%y-%H%M")
TIMESTAMP := $(shell date "+%Y%m%d%H%M%S")
SNAPSHOT_TAG := $(TIMESTAMP)$(shell git rev-parse --short HEAD | cut -c1-7)
USER_ID := $(shell id -u)
CONTAINER_TOOL ?= docker
ENTRYPOINT_COMMAND ?= langchain serve --host 0.0.0.0

virtual-env:
	python3 -m venv .venv
	source .venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements.txt

install: virtual-env
	

golden-build:
	export DOCKER_BUILDKIT=1
	$(CONTAINER_TOOL) build --network host -f golden-images/py312.dockerfile -t 044846299318.dkr.ecr.us-east-1.amazonaws.com/cognitive/golden:${SNAPSHOT_TAG} ./

golden-push: aws-login
	$(CONTAINER_TOOL) build --network host -f golden-images/py312.dockerfile -t 044846299318.dkr.ecr.us-east-1.amazonaws.com/cognitive/golden:${SNAPSHOT_TAG} ./
	$(CONTAINER_TOOL) push 044846299318.dkr.ecr.us-east-1.amazonaws.com/cognitive/golden:${SNAPSHOT_TAG}
	$(CONTAINER_TOOL) image tag 044846299318.dkr.ecr.us-east-1.amazonaws.com/cognitive/golden:${SNAPSHOT_TAG} 044846299318.dkr.ecr.us-east-1.amazonaws.com/cognitive/golden:latest
	$(CONTAINER_TOOL) push 044846299318.dkr.ecr.us-east-1.amazonaws.com/cognitive/golden:latest

local-docker: aws-login
ifeq ($(CONTAINER_TOOL), podman)
	podman machine init
	podman machine start
	USER_ID=${USER_ID} ENTRYPOINT_COMMAND="$(ENTRYPOINT_COMMAND)" podman-compose up
else
	export DOCKER_BUILDKIT=1
	$(CONTAINER_TOOL) build -f Dockerfile.dev -t ai/cognitive-service . --build-arg USER_ID=${USER_ID}
	USER_ID=${USER_ID} ENTRYPOINT_COMMAND="$(ENTRYPOINT_COMMAND)" $(CONTAINER_TOOL) compose up
endif
local-venv:
	python3 -m venv .venv
	source .venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements_no_docker.txt
run-ruff:
	ruff check ./ --fix