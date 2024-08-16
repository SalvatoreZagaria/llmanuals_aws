import * as interceptor from "./interceptor.js";

const apiUrl = interceptor.apiUrl;

window.onload = async function() {
    interceptor.overrideFetch();

    getAgentStatus();
    getOrganization();

    var intervalId = window.setInterval(function() {
        if (interceptor.idToken) {
            getAgentStatus(false);
        }
    }, 10000);

    document.getElementById("showStaticContainer").addEventListener('click', function(e) {
        const staticContainer = document.getElementById('staticContainer');
        const webContainer = document.getElementById('webContainer');
        staticContainer.style.display = 'block';
        webContainer.style.display = 'none';

        document.getElementById('showStaticContainerLi').classList.add("active");
        document.getElementById('showWebContainerLi').classList.remove("active");
    });

    document.getElementById("showWebContainer").addEventListener('click', function(e) {
        const staticContainer = document.getElementById('staticContainer');
        const webContainer = document.getElementById('webContainer');
        staticContainer.style.display = 'none';
        webContainer.style.display = 'block';

        document.getElementById('showStaticContainerLi').classList.remove("active");
        document.getElementById('showWebContainerLi').classList.add("active");
    });

    document.getElementById("enableKnowledge").addEventListener('click', function(e) {
        enableKnowledge();
    });

    document.getElementById("disableKnowledge").addEventListener('click', function(e) {
        disableKnowledge();
    });

    $('#staticModal').on('shown.bs.modal', function (e) {
        fillStaticModal();
    });

    $('#webModal').on('shown.bs.modal', function (e) {
        fillWebModal();
    });

    document.getElementById("orgDescription").addEventListener('change', function(e) {
        document.getElementById('updateOrgButton').disabled = false;
    });
    document.getElementById("orgName").addEventListener('change', function(e) {
        document.getElementById('updateOrgButton').disabled = false;
    });

    document.getElementById('updateOrgButton').addEventListener('click', function(e) {
        updateProfile();
    });

    document.getElementById('updateOrgButton').disabled = true;

    document.getElementById('deleteOrgButton').addEventListener('click', function(e) {
        deleteProfile();
    });

    document.getElementById('inputStaticFileUpload').addEventListener('change', function(event) {
        var fileName = event.target.files[0].name;
        var label = document.querySelector('label[for="inputStaticFileUpload"]');
        label.textContent = fileName;
    });

    document.getElementById('uploadFile').addEventListener('click', function() {
        var input = document.getElementById('inputStaticFileUpload');
        var file = input.files[0];

        if (file) {
            uploadFile(file);
        } else {
            alert('Please select a file to upload.');
        }
    });

    document.getElementById('updateWebLinksButton').addEventListener('click', function(e) {
        updateWebLinks();
    });

    document.getElementById('syncWebDataSource').addEventListener('click', function() {
        syncWebDataSource();
    });

    document.getElementById('syncStaticDataSource').addEventListener('click', function() {
        syncStaticDataSource();
    });

    document.getElementById('startCrawl').addEventListener('click', function() {
        startCrawl();
    });

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


function processAgentStatus(result) {
    document.getElementById('agent_status').innerText = result['agent']['agentStatus'];
    document.getElementById('kb_status').innerText = `${result['knowledge']['knowledgeBaseStatus']} (${result['knowledge']['knowledgeBaseState']})`;

    let element_id;
    let ds_status;
    let sync;
    for(let key in result['knowledge']['dataSources']){
        ds_status = result['knowledge']['dataSources'][key]['status']
        if (key == 'static') {
            element_id = 's3_status';
            sync = `(SYNC: ${result['knowledge']['dataSources'][key]['synchronization']['status']})`
        } else if (key == 'web') {
            element_id = 'web_status';
            sync = `(SYNC: ${result['knowledge']['dataSources'][key]['synchronization']['status']} - CRAWL: ${result['knowledge']['dataSources']['web']['crawling']['status']})`
        }
        document.getElementById(element_id).innerText = `${ds_status} ${sync}`;
    }
}


async function getAgentStatus(useLoader = true) {
    const response = await fetch(`${apiUrl}/api/admin/agent/status`, { method: 'GET' }, useLoader);
    const result = await response.json();
    processAgentStatus(result);
}

async function getOrganization() {
    const response = await fetch(`${apiUrl}/api/admin/organization`, { method: 'GET' });
    const result = await response.json();

    document.getElementById('orgName').value = result['organizationName'];
    document.getElementById('orgDescription').value = result['organizationDescription'];
}

async function disableKnowledge() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/disable`, { method: 'POST' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
        return
    }
    location.reload(true);
}

async function enableKnowledge() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/enable`, { method: 'POST' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
        return
    }
    location.reload(true);
}

async function syncStaticDataSource() {
    const url = '/api/admin/knowledge/static/sync';
    await syncDataSource(url);
}

async function syncWebDataSource() {
    const url = '/api/admin/knowledge/web/sync';
    await syncDataSource(url);
}

async function syncDataSource(url) {
    const response = await fetch(`${apiUrl}${url}`, { method: 'PUT' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
        return
    }
    location.reload(true);
}

async function deleteKnowledgeFile(file) {
    if (!confirm(`${file} will be deleted permanently. Are you sure?`)) {
      return
    }
    const response = await fetch(
        `${apiUrl}/api/admin/knowledge/static/delete-file?fileName=${file}`,
        {
            method: 'DELETE',
            headers: {
                "Content-Type": "application/json"
            }
        }
    );
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
        throw new Error(result.message);
    }
}

async function uploadFile(file) {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/static/get-upload-link?fileName=${file.name}`);
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
        throw new Error(result.message);
    }
    const result = await response.json();
    const uploadUrl = result['presignedUrl'];

    var xhr = new XMLHttpRequest();
    xhr.open('PUT', uploadUrl, true);
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.onload = () => {
      if (xhr.status === 200) {
        console.log('File uploaded successfully');
        fillStaticModal();
      }
    };
    xhr.onerror = () => {
      console.log('File upload failed');
    };
    xhr.send(file);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        var percent = Math.round((event.loaded / event.total) * 100)
        console.log(percent);
      }
    };
}

async function listKnowledgeFiles() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/static/list`);
    const result = await response.json();
    if (!response.ok) {
        window.alert(result.message);
        throw new Error(result.message);
    }
    return result;
}

async function updateWebLinks() {
    const urlInputs = document.querySelectorAll('[data-web-data-source-url]');
    let urls = [];
    urlInputs.forEach((i) => {
      urls.push(i.value);
    });
    const response = await fetch(
        `${apiUrl}/api/admin/knowledge/web/update`,
        {
            method: 'POST',
            body: JSON.stringify({
                urls: urls
            })
        }
    );
    if (!response.ok) {
        window.alert(result.message);
        throw new Error(result.message);
    }
    fillWebModal();
}

async function startCrawl() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/web/crawl`, { method: 'PUT' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function listWebLinks() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/web/list`);
    let urls;
    if (!response.ok && response.status == 404) {
        urls = [];
    } else if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
        throw new Error(result.message);
    } else {
        const result = await response.json();
        urls = result['urls'];
    }

    return urls;
}

async function deleteProfile() {
    if (!confirm(`Your profile is going to be deleted. This action is irreversible. Are you sure?`)) {
      return
    }
    const response = await fetch(`${apiUrl}/api/admin/organization/delete-profile`, { method: 'DELETE' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function updateProfile() {
    const description = document.getElementById("orgDescription").value;
    const name = document.getElementById("orgName").value;
    const response = await fetch(
        `${apiUrl}/api/admin/organization/update`,
        {
            method: 'POST',
            body: JSON.stringify({
                organization_name: name,
                organization_description: description
            })
        }
    );
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
        throw new Error(result.message);
    }
    location.reload(true);
}

function getUrlInput(text) {
    const div1 = document.createElement("div");
    div1.classList.add("input-group", "mb-3");
    const input = document.createElement("input");
    input.classList.add("form-control");
    input.type = "text";
    input.value = text;
    input.setAttribute("data-web-data-source-url", true);
    input.addEventListener('input', function(e) {
        document.getElementById('updateWebLinksButton').disabled = false;
    });
    const div2 = document.createElement("div");
    div1.classList.add("input-group-prepend");
    const button = document.createElement("button");
    button.type = "button";
    button.classList.add("btn", "btn-outline-secondary");
    button.innerText = 'Remove';
    button.addEventListener('click', function(e) {
        div1.remove();
        document.getElementById('updateWebLinksButton').disabled = false;
    });
    div2.appendChild(button);
    div1.appendChild(input);
    div1.appendChild(div2);

    return div1;
}

async function fillWebModal() {
    const result = await listWebLinks();
    const container = document.getElementById("staticWebListContainer");
    const ul = document.createElement("ul");
    const mainDiv = document.createElement("div");
    mainDiv.id = 'staticWebUrlsList'
    let div;
    container.innerHTML = '';
    for (const url of result) {
        div = getUrlInput(url);
        mainDiv.appendChild(div);
    }
    container.appendChild(mainDiv);
    div = document.createElement("div");
    div.style = "text-align: center; justify-content: center; align-items: center";
    const addButton = document.createElement("button");
    addButton.type = "button";
    addButton.classList.add("btn", "btn-outline-secondary", "mb-3");
    addButton.innerText = "+";
    addButton.addEventListener('click', function(e) {
        document.getElementById("staticWebUrlsList").appendChild(getUrlInput(''));
    });
    div.appendChild(addButton)
    container.appendChild(div);

    document.getElementById('updateWebLinksButton').disabled = true;
}

async function fillStaticModal() {
    const result = await listKnowledgeFiles();
    const container = document.getElementById('staticFilesListContainer');
    const ul = document.createElement("ul");
    let li;
    let span;
    let button;
    for (const file of result['files']) {
        li = document.createElement("li");
        span = document.createElement("span");
        button = document.createElement("button");
        span.innerText = file;
        button.innerText = 'X';
        button.addEventListener('click', function(e) {
            deleteKnowledgeFile(file);
        });
        button.style.float = 'right';
        button.style.marginRight = '5%';
        li.appendChild(span);
        li.appendChild(button);
        ul.appendChild(li);
    }
    container.innerHTML = '';
    container.appendChild(ul);
}
