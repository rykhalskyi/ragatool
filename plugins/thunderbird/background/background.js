  
import {WebSocketClient} from '/mainPopup/client.js';
import { get_commands, find_command } from '/mainPopup/commands.js';

console.log('Ragatouille background task');
let connected = false;
let client = null;
let entity_name = 'All email acconts on this instance'

messenger.runtime.onMessage.addListener((message) => {
    if (message.command === "connect") {
        connect();
    }
});

function connect() {
    console.log("** CONNECT **");

    if (!connected) {
        client = new WebSocketClient('ws://localhost:8000/extensions/ws');

        client.onOpen = () => {
            connected = true;
            messenger.runtime.sendMessage({ command: "updateStatus", status: connected });

            const payload = get_commands(entity_name);
            client.send(JSON.stringify({ type: "ping", payload: payload }));
        };

        client.onClose = () => {
            connected = false;
            client = null;
            messenger.runtime.sendMessage({ command: "updateStatus", status: connected });
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
                case "error":
                    console.error("Error Message from server", message.message);    
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