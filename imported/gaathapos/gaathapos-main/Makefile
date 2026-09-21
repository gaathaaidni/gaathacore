.PHONY: up build down build-web logs logs-web logs-db logs-worker logs-beat logs-flower migrate seed shell test smoke backup-pg backup-sqlite run-local

# 🐳 Docker Lifecycle
up:
	docker-compose up -d

build:
	docker-compose up --build -d

down:
	docker-compose down

build-web:
	docker-compose up --build -d web

# 📋 Logs & Debugging
logs:
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-db:
	docker-compose logs -f db

logs-worker:
	docker-compose logs -f worker

logs-beat:
	docker-compose logs -f beat

logs-flower:
	docker-compose logs -f flower

# 🗄️ Database Management
migrate:
	docker-compose exec web flask db upgrade

seed:
	docker-compose exec web python seed.py

shell:
	docker-compose exec web /bin/bash

# 🧪 Testing
test:
	docker-compose exec web pytest

smoke:
	docker-compose exec web python smoke_test.py

# 💾 Backups
backup-pg:
	./pg_backup.sh

backup-sqlite:
	python export_sqlite_csv.py

# 💻 Local Development
run-local:
	python app.py