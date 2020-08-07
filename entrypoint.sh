#!/bin/sh

set -e

. /venv/bin/activate

ez-sendgrid "$@"
