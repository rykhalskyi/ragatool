import { get_commands } from './commands.js';

let client = null;
let connected = false;
let file_name = "";

function connectClick() {
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
                default:
                    console.warn("Unknown message type:", message.type);
            }

            // You can call any plugin API method from here.
            // For example, let's get the editor version as you asked.
            try {
                // IMPORTANT: Wait for the plugin to be fully initialized before making API calls.
                await isPluginReady;
                const version = await Editor.callMethod("GetVersion");
                console.log("Editor version:", version);

                // You could also execute a command, for example, to insert text:
                // await Editor.callCommand(function() {
                //     var oDocument = Api.GetDocument();
                //     var oParagraph = Api.CreateParagraph();
                //     oParagraph.AddText("Received: " + event.data);
                //     oDocument.InsertContent([oParagraph]);
                // });

            } catch (error) {
                console.error("Error calling API method from WebSocket handler:", error);
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

(function(window, undefined){

    window.Asc.plugin.init = async function()
    {
        console.log('begin');
        try {
            const fileName = await Editor.callCommand(function() {
                // This code runs in the editor's context
                return Api.GetFullName();
            });
            console.log("Successfully got file name:", fileName);
            // You can now use the fileName variable, for example:
            // Asc.scope.fileName = fileName; 
            // Or display it in your plugin's UI
            file_name = fileName;
        } catch (error) {
            console.error("Error getting file name on init:", error);
        }
        console.log('end');
        // Signal that the plugin API is ready.
        pluginReadyResolver();
    };

})(window, undefined);

window.connectClick = connectClick;
