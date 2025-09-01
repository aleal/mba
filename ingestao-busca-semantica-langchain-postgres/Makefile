python-env:
	@if [ ! -d "venv" ]; then \
		python3 -m venv venv; \
	fi
	./venv_activate.sh
	pip install -r requirements.txt

pg-up:
	docker compose up -d

pg-down:
	docker compose down

ingest:
	python src/ingest.py

chat:
	python src/chat.py

run:
	make python-env
	make pg-up
	make ingest
	make chat
	make pg-down

   