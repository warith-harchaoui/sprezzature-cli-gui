FROM python:3.11-slim

LABEL maintainer="warithmetics@deraison.ai"
LABEL description="sprezzature-cli-gui: turn a Python CLI (argparse/Click/Typer) into a single-file HTML GUI"

WORKDIR /app

COPY . .

# One install brings everything this image serves: Click and Typer, so a
# mounted Click or Typer CLI can be read, and fastapi, uvicorn and fastapi-mcp
# for the HTTP and MCP surfaces. They are all base dependencies since
# 2026-11-01; there is no extra to ask for.
RUN pip install --no-cache-dir "."

EXPOSE 8000

# Serve what the image was built for. A CMD of `--help` is a container that
# starts, prints and exits — which looks like it works and does nothing.
# Override with the command line:
#
#   docker run --rm -v "$PWD:/work" -e PYTHONPATH=/work IMAGE \
#       sprezzature-cli-gui mytool.cli:build_parser --out /work/gui.html
CMD ["uvicorn", "sprezzature_cli_gui.api:app", "--host", "0.0.0.0", "--port", "8000"]
