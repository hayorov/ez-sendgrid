FROM python:3-slim as builder

COPY . .
RUN pip install -U --no-cache-dir --disable-pip-version-check -q poetry \
    && python -m venv /venv \
    && poetry export -f requirements.txt | /venv/bin/pip install -r /dev/stdin \
    && poetry build && /venv/bin/pip install dist/*.whl

FROM python:3-alpine as base
ADD . /app
WORKDIR /app

RUN apk add --no-cache py3-cryptography

COPY --from=builder /venv /venv
COPY entrypoint.sh ./

RUN . /venv/bin/activate

ENTRYPOINT ["./entrypoint.sh"]
CMD ["--", "--help"]
