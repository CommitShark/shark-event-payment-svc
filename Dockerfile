FROM python:3.12-slim

WORKDIR /app

# Install bash and any needed packages
RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt -e .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/init.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# Your original command becomes the default CMD
CMD [ "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.interfaces.fastapi.app:app", "--bind", "0.0.0.0:80", "--access-logfile", "-","--error-logfile", "-"]
