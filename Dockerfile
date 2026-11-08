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

# A page is compiled with Tailwind's standalone CLI, about 45 MB. In the image,
# not on a container's first page: a `docker run --rm` has no cache to keep it
# in, and would fetch it every time. Compiling one class here also proves the
# binary runs on this base image, and a failed download stops the build instead
# of shipping an image that needs GitHub at run time.
ENV SPREZZATURE_CLI_GUI_CACHE=/opt/sprezzature-cli-gui/cache
RUN python -c "from sprezzature_cli_gui.tailwind import stylesheet; print(stylesheet(['<p class=flex></p>']).version)"

EXPOSE 8000

# Serve what the image was built for: the MCP server, which is the same FastAPI
# app as the HTTP routes with /mcp mounted on it, so one container answers both
# /v1/... and /mcp on one port. Serving `api:app` with uvicorn directly would
# leave /mcp out, because the endpoint is mounted when mcp.py is imported.
# A CMD of `--help` is a container that
# starts, prints and exits — which looks like it works and does nothing.
# Override with the command line:
#
#   docker run --rm -v "$PWD:/work" -e PYTHONPATH=/work IMAGE \
#       sprezzature-cli-gui mytool.cli:build_parser --out /work/gui.html
CMD ["sprezzature-cli-gui-mcp", "--host", "0.0.0.0", "--port", "8000"]
