# Convenience targets for the Prediction League platform.
# On Windows without `make`, use scripts/ or the raw `docker compose` commands.

.PHONY: up down logs ps clean rebuild help

help:
	@echo "Targets: up | down | logs | ps | clean | rebuild"

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
