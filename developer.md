# Developer Guide

## Compile protobuf files to python

```bash
# Reservation
python -m grpc_tools.protoc -I proto --python_out=./app/infrastructure/grpc --grpc_python_out=./app/infrastructure/grpc --pyi_out=./app/infrastructure/grpc proto/ticketing.proto

# User
python -m grpc_tools.protoc -I proto --python_out=./app/infrastructure/grpc --grpc_python_out=./app/infrastructure/grpc --pyi_out=./app/infrastructure/grpc proto/user.proto
```

## Install & Configure CLI

```bash
source .venv/bin/activate && pip install -r requirements.txt -e .
```

## Run Background worker

```bash
python -m app.infrastructure.worker.bootstrap
```
