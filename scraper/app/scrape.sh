#!/bin/bash

if [ $# -ne 2 ]
  then
    echo "./scrape <url> <bucket_prefix>"
    exit 1
fi

service tor start
service privoxy start

URL="$1"
BUCKET_PREFIX="$2"

echo "URL: $URL"
echo "BUCKET_PREFIX: $BUCKET_PREFIX"

source /.venv/bin/activate
python main.py "$URL" "$BUCKET_PREFIX"
deactivate


# shellcheck disable=SC2046
kill -9 $(pidof tor)
service privoxy stop

exit 0
