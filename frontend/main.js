import * as interceptor from "./interceptor.js";

const websocketEndpoint = 'wss://rzdd5r57y7.execute-api.eu-west-2.amazonaws.com/dev';
let websocket;

window.onload = async function() {
    interceptor.overrideFetch();
    await interceptor.refreshTokens();
    connect();

    document.getElementById('prompt').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            query();
            e.preventDefault();
        }
    });
    document.getElementById('sendQuery').addEventListener('click', function(e) {
        query();
    });

    var tooltips = document.querySelectorAll('.tooltip span');
    window.onmousemove = function (e) {
        var x = e.clientX + 'px',
            y = e.clientY + 'px';
        for (var i = 0; i < tooltips.length; i++) {
            tooltips[i].style.top = y;
            tooltips[i].style.left = x;
        }
    };

    document.getElementById('sendLoginButton').addEventListener('click', async function() {
        await interceptor.login();
    });

    document.getElementById('inputEmail').addEventListener('keydown', async function(e) {
        if (e.key === 'Enter') {
            await interceptor.login();
            e.preventDefault();
        }
    });

    document.getElementById('inputPassword').addEventListener('keydown', async function(e) {
        if (e.key === 'Enter') {
            await interceptor.login();
            e.preventDefault();
        }
    });
};


function processAssistantMessage(data) {
    data = JSON.parse(data);
    if (data.type == 'start' || data.type == 'end') {
        return ''
    }
    if (data.type == 'error') {
        window.alert(data.message);
        throw new Error(data.message);
    }
    if (data.type == 'message') {
        let ret = data.message
        for (const ref of data.references) {
            ret = `${ret} <div class="tooltip"><a href="${ref.link}" target="_blank">source</a><span class="tooltiptext">"${ref.text}"</span></div>`
        }
        return ret;
    } else {
        throw new Error('Unhandled case');
    }
}


function connect() {
    let accessToken = localStorage.getItem('jwtAccessToken');
    websocket = new WebSocket(websocketEndpoint + '?accessToken=' + accessToken);

    websocket.onopen = function(event) {
        console.log('Connected to WebSocket');
    };

    websocket.onclose = function(event) {
        console.log('Disconnected from WebSocket');
    };

    websocket.onmessage = function(event) {
        var responseDiv = document.getElementById('response');

        responseDiv.innerHTML = responseDiv.innerHTML + processAssistantMessage(event.data);
        console.log('Message received: ', event.data);
    };

    websocket.onerror = function(event) {
        console.error('WebSocket error: ', event);
    };
}

function disconnect() {
    if (websocket) {
        websocket.close();
    }
}

function query() {
    const prompt = document.getElementById('prompt').value;
    if (!prompt) {
        alert('No query!');
        return
    }
    const responseDiv = document.getElementById('response');

    const messagePayload = {
        action: 'query',
        prompt: prompt
    };

    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify(messagePayload));
        console.log('Sent query request');
        responseDiv.classList.remove('collapse');
        responseDiv.innerHTML = '';
    } else {
        console.error('WebSocket is not connected');
        displayMessage('WebSocket is not connected');
    }
}
