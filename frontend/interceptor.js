const client_id = '1gninisvq5bhg0dj88i0dfuv55';
const cognitoUrl = 'https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_JUVPtjO37';
export const apiUrl = 'https://yoimepyn0c.execute-api.eu-west-2.amazonaws.com/dev';

export let idToken = localStorage.getItem('jwtIdToken');

export function promptLogin() {
    $('#loginModal').modal('show');
}

export async function login() {
    const email = document.getElementById('inputEmail').value;
    const passw = document.getElementById('inputPassword').value;
    if (!email || !passw) {
        alert('Insert email and password.');
        return
    }
    const headers = {
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
        'Content-Type': 'application/x-amz-json-1.1'
    };

    const data = {
        'ClientId': client_id,
        'AuthFlow': 'USER_PASSWORD_AUTH',
        'AuthParameters': {
            'USERNAME': email,
            'PASSWORD': passw
        }
    };

    try {
        const response = await originalFetch(cognitoUrl, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });

        let json = await response.json();
        localStorage.setItem('jwtIdToken', json.AuthenticationResult.IdToken);
        localStorage.setItem('jwtAccessToken', json.AuthenticationResult.AccessToken);
        localStorage.setItem('jwtRefreshToken', json.AuthenticationResult.RefreshToken);
        idToken = json.AuthenticationResult.IdToken;
    } catch (error) {
        console.error('Error:', error);
    }
    $('#loginModal').modal('hide');
}


export async function customFetch(url, options = {}, useLoader = true) {
    if (useLoader) {
        showLoader();
    }

    if (!idToken) {
        let res = await refreshTokens();
        if (!res) {
            dismissLoader();
            return Promise.reject('No refresh token available');
        }
    }

    options.headers = {
        ...options.headers,
        'Authorization': idToken
    };
    try {
        let response = await originalFetch(url, options);
        if (response.status === 401) {
            let res = await refreshTokens();
            if (res) {
                options.headers.Authorization = idToken;
                response = await originalFetch(url, options);
                dismissLoader();
                return response;
            } else {
                dismissLoader();
                return Promise.reject('No refresh token available');
            }
        }
        dismissLoader();
        return response;
    } catch (e) {
        console.error(e);
        let res = await refreshTokens();
        if (res) {
            options.headers.Authorization = idToken;
            response = await originalFetch(url, options);
            dismissLoader();
            return response;
        } else {
            dismissLoader();
            return Promise.reject('No refresh token available');
        }
    }
};

function showLoader() {
    document.getElementById('loaderWheel').style.display = 'block';
    document.getElementById('loaderOverlay').style.display = 'flex';
}

function dismissLoader() {
    document.getElementById('loaderWheel').style.display = 'none';
    document.getElementById('loaderOverlay').style.display = 'none';
}


export async function refreshTokens() {
    const refreshToken = localStorage.getItem('jwtRefreshToken');
    if (!refreshToken) {
        promptLogin();
        return false;
    }
    const headers = {
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
        'Content-Type': 'application/x-amz-json-1.1'
    };

    const data = {
        'ClientId': client_id,
        'AuthFlow': 'REFRESH_TOKEN',
        'AuthParameters': {
            'REFRESH_TOKEN': refreshToken
        }
    };

    try {
        const response = await originalFetch(cognitoUrl, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });

        let json = await response.json();
        localStorage.setItem('jwtIdToken', json.AuthenticationResult.IdToken);
        localStorage.setItem('jwtAccessToken', json.AuthenticationResult.AccessToken);
        idToken = json.AuthenticationResult.IdToken;
        return true;
    } catch (error) {
        console.error('Error:', error);
        promptLogin();
        return false;
    }
}

export function overrideFetch() {
    window.originalFetch = window.fetch;
    window.fetch = customFetch;
}
