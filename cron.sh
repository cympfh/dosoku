#!/bin/bash

URL=$(cat config.json | jq -r .slack.incoming)

post() {
    USERNAME=$1
    ICON=$2
    COLOR=$3
    shift 3
    TEXT=$(echo "$@" | tr '\n' '\t' | sed 's/[\t ]*$//g; s/\t/\\n/g')
    PAYLOAD=$(mktemp)
    cat <<EOM >$PAYLOAD
{
    "username": "${USERNAME}",
    "icon_emoji": ":${ICON}:",
    "channel": "#timeline",
    "fallback": "Hi",
    "color": "${COLOR}",
    "fields": [
        {
            "title": "",
            "value": "${TEXT}",
            "short": true
        }
    ]
}
EOM
    curl "$URL" --data @$PAYLOAD
    rm $PAYLOAD
}

post-tenki() {
    post tenki partly_sunny "#ff6060" "$(tenki)"
    post tenki partly_sunny "#ff6060" "$(tenki -f)"
}

post-anime() {
    post animetick tv "#44aa88" "$(animetick)"
}

while :; do
    atq 10:30 echo "ITS TIME" && (
        post-tenki
        post-anime
    )
    sleep 2h
done
