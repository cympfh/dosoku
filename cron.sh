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
    post animetick tv "#44aa88" "$(animetick -D)"
}

work() {
    post-tenki
    post-anime
}

while :; do
    atq 8:00 echo && work
    atq 10:00 echo && work
    atq 12:00 echo && work
    atq 14:00 echo && work
    atq 16:00 echo && work
    atq 18:00 echo && work
    atq 20:00 echo && work
    atq 22:00 echo && work
    sleep 3h
done
