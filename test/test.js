const websocketEndpoint = 'wss://rzdd5r57y7.execute-api.eu-west-2.amazonaws.com/dev';
let websocket;

function connect() {
    websocket = new WebSocket(websocketEndpoint);

    websocket.onopen = function(event) {
        console.log('Connected to WebSocket');
    };

    websocket.onclose = function(event) {
        console.log('Disconnected from WebSocket');
    };

    websocket.onmessage = function(event) {
        var responseDiv = document.getElementById('response');
        responseDiv.innerHTML = responseDiv.innerHTML + '<p>' + event.data + '</p><br>';
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
    const messagePayload = {
        action: 'query'
    };

    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify(messagePayload));
        console.log('Sent query request');
        var responseDiv = document.getElementById('response');
        responseDiv.innerHTML = '';
    } else {
        console.error('WebSocket is not connected');
        displayMessage('WebSocket is not connected');
    }
}

window.onload = (event) => {
    connect();
    document.getElementById("queryButton").addEventListener('click', function(e) {
        query();
    })
};
