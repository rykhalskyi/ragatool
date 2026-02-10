import {WebSocketClient} from './client.js'
import { get_commands } from './commands.js';

console.log('Hello, World! - from popup.js');

let client = null;
let connected = false;
let file_name = "";

function connectClick(event) {
    console.log("CONNECT CLICK");

    const statusElement = document.getElementById('status');
    const connectButton = document.getElementById('connectBtn');

    if (!connected) {
        client = new WebSocketClient('ws://localhost:8000/extensions/ws');

        client.onOpen = () => {
            statusElement.textContent = 'Connected';
            connectButton.textContent = 'Disconnect';
            connected = true;

            const payload = get_commands(file_name);
            client.send(JSON.stringify({ type: "ping", payload: payload }));
        };

        client.onClose = () => {
            statusElement.textContent = 'Disconnected';
            connectButton.textContent = 'Connect';
            connected = false;
            client = null;
        };

        client.onError = (error) => {
            console.error('WebSocket Error:', error);
            statusElement.textContent = 'Error connecting';
        };

        client.onMessage = async (event) => {
            console.log('Message from server:', event.data);
            const message = JSON.parse(event.data);

            switch (message.topic) {
                case "ping":
                    console.log("Ping payload:", message.payload);
                    client.send(JSON.stringify({type: "pong", payload: message.timestamp}));
                    break;
                case "call_command":
                    const command = find_command(message.id);
                    if (command !== undefined)
                    {
                      const result = await command.do(message.message);
                      client.send(JSON.stringify({
                        type: "command_response",
                        correlation_id: message.correlation_id, 
                        payload: result}))
                    }
                default:
                    console.warn("Unknown message type:", message.type);
            }

        };

        client.connect();
    } else {
        if (client) {
            client.disconnect();
        }
    }
}

document.getElementById('connectBtn').addEventListener('click', connectClick);