#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No urls supplied"
    exit 1
fi

if [[ -z "${USER_ID}" ]]; then
  echo "USER_ID env variable must be set"
  exit 1
fi
echo "USER_ID: $USER_ID"

# shellcheck disable=SC2317
function scrape() {
  # shellcheck disable=SC2048
  for URL in $*
  do
    echo "Scraping $URL..."
    /.venv/bin/python scrape.py --url "$URL"
  done
}
export -f scrape

service tor start
service privoxy start

timeout 10800 bash -c "USER_ID=$USER_ID scrape $*" # Stopping after 3 hours
EXIT_STATUS=$?
if [ $EXIT_STATUS -eq 124 ]
then
  STATUS='TIMEOUT'
elif [ $EXIT_STATUS -eq 0 ]; then
  STATUS='SUCCEEDED'
  /.venv/bin/python upload_to_s3.py
else
  STATUS='FAILED'
fi
echo "Status: $STATUS"

/.venv/bin/python update_task_status.py --status "$STATUS"

# shellcheck disable=SC2046
kill -9 $(pidof tor)
service privoxy stop

exit 0
