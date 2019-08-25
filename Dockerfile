FROM python:3-alpine

RUN pip install poetry

ADD . /app

WORKDIR /app

RUN poetry config settings.virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

ENTRYPOINT ["ez-sendgrid"]
CMD ["--", "--help"]
