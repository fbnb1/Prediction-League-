# Convenience targets for the Prediction League platform.
# On Windows without `make`, use scripts/ or the raw `docker compose` commands.

.PHONY: up down logs ps clean rebuild test e2e help

help:
	@echo "Targets: up | down | logs | ps | clean | rebuild | test | e2e"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v

rebuild:
	docker compose build --no-cache

test:
	docker compose --profile test run --rm ledger-tests
	docker compose --profile test run --rm fixture-tests
	docker compose --profile test run --rm prediction-tests

e2e:
	bash scripts/e2e-demo.sh
