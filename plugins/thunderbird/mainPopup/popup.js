console.log('Hello, World! - from popup.js');


function connectClick(event) {
    console.log("CONNECT CLICK");
    const tokenInput = document.getElementById('token');
    const token = tokenInput ? tokenInput.value.trim() : '';
    if (token) {
        localStorage.setItem('ragatool_token', token);
    }
    messenger.runtime.sendMessage({ command: "connect", token });
}

const tokenInput = document.getElementById('token');
if (tokenInput) {
    tokenInput.value = localStorage.getItem('ragatool_token') || '';
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


