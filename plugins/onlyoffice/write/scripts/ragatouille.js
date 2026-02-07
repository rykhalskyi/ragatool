import { find_command, get_commands } from './commands.js';

let client = null;
let connected = false;
let file_name = "";

function connectClick() {
    console.log('CONNECT CLICK');
    const statusElement = document.getElementById('status');
    const connectButton = document.querySelector('button');

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

let pluginReadyResolver;
const isPluginReady = new Promise(resolve => {
    pluginReadyResolver = resolve;
});

var Editor = {
    callCommand : async function(func) {
        return new Promise(resolve => (function(){
            window.Asc.plugin.callCommand(func, false, true, function(returnValue){
                resolve(returnValue);
            });
        })());
    },
    callMethod : async function(name, args)
    {
        return new Promise(resolve => (function(){
            window.Asc.plugin.executeMethod(name, args || [], function(returnValue){
                resolve(returnValue);
            });
        })());
    }
};

// export { Editor };

// Attach Editor to window so it is globally accessible
window.Editor = Editor;

(function(window, undefined){
  console.log('START', window.Editor);
    window.Asc.plugin.init = async function()
    {
        console.log('INIT');
        try {
            const fileName = await Editor.callCommand(function() {

                // This code runs in the editor's context
                return Api.GetFullName();
            });
            // You can now use the fileName variable, for example:
            // Asc.scope.fileName = fileName; 
            // Or display it in your plugin's UI
            file_name = fileName;
            console.log('FILE NAME',file_name);
        } catch (error) {
            console.error("Error getting file name on init:", error);
        }
        pluginReadyResolver();
    };

})(window, undefined);

window.connectClick = connectClick;
