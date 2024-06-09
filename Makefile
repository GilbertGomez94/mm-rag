virtual-env:
	python3 -m venv .venv
	source .venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements.txt

install: virtual-env

run-chat-app:
	chainlit run chat/main.py --port 8081 -w

run-server:
	uvicorn server.appmm:app --reload

condainstall:
	pip install --upgrade pip
	pip install -r requirements.txt