FROM python:3.12-bookworm

RUN pip install poetry==1.8.3

WORKDIR /pivottrack

COPY pyproject.toml poetry.lock ./
COPY pivot_track ./pivot_track
RUN touch README.md

RUN poetry install

ENTRYPOINT ["poetry", "run", "pivottrack", "track"]