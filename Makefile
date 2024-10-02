up:
	docker compose up --build
	
up-rebuild:
	docker compose up --no-deps --build 

backend:
	docker compose up --build backend

down:
	docker compose down

down-prune:
	docker compose down --volumes

migrate-session:
	docker compose exec backend python -m alembic revision --autogenerate -m "Create users and sessions tables"
	docker compose exec backend python -m alembic upgrade head

migrate-model:
	docker compose exec backend python -m alembic revision --autogenerate -m "Add UserModelConfig table"
	docker compose exec backend python -m alembic upgrade head

.PHONY: up up-rebuild down down-prune dev dev backend migrate-session migrate-model