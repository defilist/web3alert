

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

fmt: ## Run black to format code
	pipenv run black .

start-dev: ## Run dump/load in local mode(only Ethereum mainnet available)
	hack/dev.sh

stop-dev: ## Stop the local development mode
	pipenv run supervisorctl shutdown
	docker-compose stop

build-image: ## Build docker image
	docker build -t jsvisa/web3alert:v$(shell date +"%Y%m%d") .

push-image: build-image ## Push docker image
	docker push jsvisa/web3alert:v$(shell date +"%Y%m%d")

test:  ## Run pytest for files under ./tests
	PYTHONPATH=. pipenv run python -m pytest tests

test-all:  ## Run pytest for all files
	PYTHONPATH=. pipenv run python -m pytest .

setup:  ## Run pipenv install to setup the environment
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev --skip-lock
	PIPENV_VENV_IN_PROJECT=1 pipenv run pre-commit install

install: ## Run pipenv install to install new pip packages
	PIPENV_VENV_IN_PROJECT=1 pipenv install --skip-lock

freeze: ## Run pip freeze to generage requirements.txt
	PIPENV_VENV_IN_PROJECT=1 pipenv run pip freeze > requirements.txt
