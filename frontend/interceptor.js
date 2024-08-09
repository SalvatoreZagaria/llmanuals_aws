const client_id = '1gninisvq5bhg0dj88i0dfuv55';
const cognitoUrl = 'https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_JUVPtjO37';
export const apiUrl = 'https://yoimepyn0c.execute-api.eu-west-2.amazonaws.com/dev';


export async function customFetch(url, options = {}) {
    let loader = document.getElementById('loaderWheel');
    let loaderOverlay = document.getElementById('loaderOverlay');
    loader.style.display = 'block';
    loaderOverlay.style.display = 'flex';
    let token = localStorage.getItem('jwtIdToken');
    if (token) {
        options.headers = {
            ...options.headers,
            'Authorization': token
        };
    } else {
        await promptLogin();
        token = localStorage.getItem('jwtIdToken');
    }

    let response = await originalFetch(url, options);

    if (response.status === 401) {
        const refreshToken = localStorage.getItem('jwtRefreshToken');
        if (refreshToken) {
            await refreshTokens(refreshToken);
            token = localStorage.getItem('jwtIdToken');
            if (!token) {
                loader.style.display = "none";
                loaderOverlay.style.display = 'none';
                await promptLogin();
                return Promise.reject('Token refresh failed');
            }
        } else {
            loader.style.display = "none";
            loaderOverlay.style.display = 'none';
            await promptLogin();
            return Promise.reject('No refresh token available');
        }
    }

    loader.style.display = "none";
    loaderOverlay.style.display = 'none';
    return response;
}

async function login(username, password) {
    const headers = {
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
        'Content-Type': 'application/x-amz-json-1.1'
    };

    const data = {
        'ClientId': client_id,
        'AuthFlow': 'USER_PASSWORD_AUTH',
        'AuthParameters': {
            'USERNAME': username,
            'PASSWORD': password
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
        location.reload(true);
    } catch (error) {
        console.error('Error:', error);
    }
}


export async function refreshTokens(refresh_token) {
    const headers = {
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
        'Content-Type': 'application/x-amz-json-1.1'
    };

    const data = {
        'ClientId': client_id,
        'AuthFlow': 'REFRESH_TOKEN',
        'AuthParameters': {
            'REFRESH_TOKEN': refresh_token
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
        return true;
    } catch (error) {
        console.error('Error:', error);
        return false;
    }
}

export async function promptLogin() {
    var email = prompt('Please enter your email');
    var password = prompt('Please enter your password');

    await login(email, password);
}

export function overrideFetch() {
    window.originalFetch = window.fetch;
    window.fetch = customFetch;
}
