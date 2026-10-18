FROM python:3.11-slim

LABEL maintainer="warithmetics@deraison.ai"
LABEL description="sprezzature-cli-gui: turn a Python CLI (argparse/Click/Typer) into a single-file HTML GUI"

WORKDIR /app

COPY . .

# The base runtime is the standard library — `requirements.txt` says so, and
# says it on purpose. What this image needs beyond that is the two adapters,
# so a mounted Click or Typer CLI can be imported at all, and the web server:
# fastapi and uvicorn live behind the `api` extra so that nobody installing
# the library pays for them. The previous `.[click,typer]` build could not
# serve the API this image exists to serve.
RUN pip install --no-cache-dir ".[click,typer,api,mcp]"

EXPOSE 8000

# Serve what the image was built for. A CMD of `--help` is a container that
# starts, prints and exits — which looks like it works and does nothing.
# Override with the command line:
#
#   docker run --rm -v "$PWD:/work" -e PYTHONPATH=/work IMAGE \
#       sprezzature-cli-gui mytool.cli:build_parser --out /work/gui.html
CMD ["uvicorn", "sprezzature_cli_gui.api:app", "--host", "0.0.0.0", "--port", "8000"]
