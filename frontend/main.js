import * as interceptor from "./interceptor.js";

const apiUrl = interceptor.apiUrl;

window.onload = async function() {
    interceptor.overrideFetch();
    await interceptor.refreshTokens();

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
    const responseDiv = document.getElementById('response_text');
    let res = '';
    for (const message of data.messages) {
        if (message.type == 'error') {
            window.alert(message.message);
            throw new Error(message.message);
        }
        if (message.type == 'message') {
            res += message.message
            for (const ref of message.references) {
                res += ` <div class="tooltip"><a href="${ref.link}" target="_blank">source</a><span class="tooltiptext">"${ref.text}"</span></div>`
            }
            res += '\n'
        } else {
            window.alert('Unhandled case');
        }
    }
    responseDiv.innerHTML = res;
}


async function query() {
    const prompt = document.getElementById('prompt').value;
    if (!prompt) {
        alert('No query!');
        return
    }

    document.getElementById('response').classList.remove('collapse');
    document.getElementById('response_text').innerHTML = '';
    document.getElementById('loaderWheel').style.display = '';

    const response = await fetch(
        `${apiUrl}/api/admin/agent/query`,
        {
            method: 'POST',
            body: JSON.stringify({
                prompt: prompt
            })
        },
        false
    );

    if (!response.ok) {
        window.alert(result.message);
        return
    }
    const result = await response.json();
    processAssistantMessage(result);
    document.getElementById('loaderWheel').style.display = 'none';
}
