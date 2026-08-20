FROM python:3.11-slim

LABEL maintainer="warith.harchaoui@gmail.com"
LABEL description="sprezzature-cli-gui: turn a Python CLI (argparse/Click/Typer) into a single-file HTML GUI"

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e ".[click,typer]"

# Default: show the tool's own --help (it needs a SPEC argument to do anything else).
CMD ["sprezzature-cli-gui", "--help"]
