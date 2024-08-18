#!/bin/bash

if [ $# != 2 ]
  then
    echo "url and task_id needed"
    exit 1
fi

if [[ -z "${USER_ID}" ]]; then
  echo "USER_ID env variable must be set"
  exit 1
fi
echo "USER_ID: $USER_ID"
URL="$1"
TASK_ID="$2"
echo "URL: $URL"
echo "TASK_ID: $TASK_ID"

service tor start
service privoxy start

source /.venv/bin/activate

python create_task_entry.py --task_id "$TASK_ID"

timeout 10800 python scrape.py --url "$URL"   # Stopping after 3 hours
EXIT_STATUS=$?
if [ $EXIT_STATUS -eq 124 ]
then
  STATUS='TIMEOUT'
elif [ $EXIT_STATUS -eq 0 ]; then
  STATUS='SUCCEEDED'
  python upload_to_s3.py
else
  STATUS='FAILED'
fi
echo "Status: $STATUS"

python update_task_status.py --status "$STATUS" --task_id "$TASK_ID"

deactivate

# shellcheck disable=SC2046
kill -9 $(pidof tor)
service privoxy stop

exit 0
