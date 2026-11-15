console.log('Hello, World! - from popup.js');


const TOKEN_STORAGE_KEY = 'ragatool_token';

function readStoredToken() {
    try {
        return sessionStorage.getItem(TOKEN_STORAGE_KEY) || '';
    } catch (error) {
        return '';
    }
}

function storeToken(token) {
    try {
        if (token) {
            sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
        } else {
            sessionStorage.removeItem(TOKEN_STORAGE_KEY);
        }
    } catch (error) {
        // Storage may be unavailable in some extension contexts.
    }
}

function connectClick(event) {
    console.log("CONNECT CLICK");
    const tokenInput = document.getElementById('token');
    const token = tokenInput ? tokenInput.value.trim() : '';
    storeToken(token);
    messenger.runtime.sendMessage({ command: "connect", token });
}

const tokenInput = document.getElementById('token');
if (tokenInput) {
    tokenInput.value = readStoredToken();
}

document.getElementById('connectBtn').addEventListener('click', connectClick);

// Check connection status on popup open
messenger.runtime.sendMessage({ command: "getStatus" });

messenger.runtime.onMessage.addListener((message) => {
    if (message.command === "updateStatus") {
        const statusElement = document.getElementById('status');
        const connectButton = document.getElementById('connectBtn');
        if (message.status) {
            statusElement.textContent = 'Connected';
            connectButton.textContent = 'Disconnect';
        } else {
            statusElement.textContent = 'Disconnected';
            connectButton.textContent = 'Connect';
        }
    }
});


