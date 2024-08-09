import * as interceptor from "./interceptor.js";

interceptor.overrideFetch();
const apiUrl = interceptor.apiUrl;

window.onload = async function() {
    await getAgentStatus();
    await getOrganization();
};


async function getAgentStatus() {
    const response = await fetch(`${apiUrl}/api/admin/agent/status`, { method: 'GET' });
    const result = await response.json();

    document.getElementById('agent_status').innerText = result['agent']['agentStatus'];
    document.getElementById('kb_status').innerText = result['knowledge']['knowledgeBaseStatus'];

    let element_id;
    for(let key in result['knowledge']['dataSources']){
        if (key == 'static') {
            element_id = 's3_status';
        } else if (key == 'web') {
            element_id = 'web_status';
        }
        document.getElementById(element_id).innerText = result['knowledge']['dataSources'][key]['status'];
    }
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
    }
}

async function enableKnowledge() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/enable`, { method: 'POST' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function deleteKnowledgeFile() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/static/delete-file`, { method: 'DELETE' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function uploadFile() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/static/get-upload-link`);
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
        return
    }
    const result = await response.json();
//    TODO
}

async function listKnowledgeFiles() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/static/list`);
    const result = await response.json();
    if (!response.ok) {
        window.alert(result.message);
        return
    }
//    TODO
}

async function syncKnowledge() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/static/sync`, { method: 'POST' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function addWebLink() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/web/add-link`, { method: 'POST' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function deleteWeb() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/web/delete`, { method: 'DELETE' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function deleteWebLink() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/web/delete-link`, { method: 'DELETE' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function listWebLinks() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/web/list`);
    const result = await response.json();
    if (!response.ok) {
        window.alert(result.message);
        return
    }
//    TODO
}

async function syncWeb() {
    const response = await fetch(`${apiUrl}/api/admin/knowledge/web/sync`, { method: 'POST' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function deleteProfile() {
    const response = await fetch(`${apiUrl}/api/admin/organization/delete-profile`, { method: 'DELETE' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}

async function updateProfile() {
    const response = await fetch(`${apiUrl}/api/admin/organization/update`, { method: 'POST' });
    if (!response.ok) {
        const result = await response.json();
        window.alert(result.message);
    }
}
