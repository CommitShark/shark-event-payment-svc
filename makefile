dev:
	uvicorn app.interfaces.fastapi.app:app --reload --port 8004

prod:
	gunicorn -k uvicorn.workers.UvicornWorker app.interfaces.fastapi.app:app \
		--bind 0.0.0.0:80 \
		--access-logfile - \
		--error-logfile -
