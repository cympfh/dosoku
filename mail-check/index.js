var fs = require('fs');
var request = require('request');
var config = require('./config.json');

// to Slack channel
function post(text) {
    headers = {
        "Content-type": "application/json"
    };
    data = {
        "username": "mail",
        "fallback": "Hi",
        "channel": "#mail",
        "text": `@channel ${text}`,
        "icon_emoji": ":email:",
        "link_names": 1
    }
    console.log('POST', data)
    options = {
        headers: headers,
        body: JSON.stringify(data)
    };
    request.post(config.webhookurl, options, (err, response) => {
        if (err) { console.log('Err from Slack:', err); }
        if (response) { console.log('Response:', response.body); }
    });
}

var num_lines = -1;

function check() {
    const path = config.path;
    fs.readFile(path, {encoding: 'utf-8'}, (err, data) => {
        if (err) {
            console.warn(err);
            return;
        }

        data = data.trim();
        const lines = data.split('\n');

        if (num_lines == -1) {
            num_lines = lines.length;
            return;
        }

        if (num_lines < lines.length) {
            console.log(`New ${lines.length - num_lines} mails`);
            for (var i = num_lines; i < lines.length; ++i) {
                const body = lines[i].split('\t')[2];
                console.log(i, body);
                post(body);
            }
            num_lines = lines.length;
        }
    });
}

check();
const interval = 30 * 1000;
setInterval(check, interval);
