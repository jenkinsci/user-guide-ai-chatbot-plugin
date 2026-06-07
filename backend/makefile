setup:
	cp .env.example .env
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt
	docker-compose up -d

# Start the application
run:
	./venv/bin/python main.py

# Stop the database
stop:
	docker-compose down