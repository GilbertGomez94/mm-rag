virtual-env:
	python3 -m venv .venv
	source .venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements.txt

install: virtual-env

run-app:
	uvicorn serverr.appmm:app --reload
	chainlit run chat/main.py --port 8081 -w

condainstall:
	pip install --upgrade pip
	pip install -r requirements.txt