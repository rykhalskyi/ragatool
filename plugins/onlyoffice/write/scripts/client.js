
class WebSocketClient {
    constructor(url, protocols = null) {
        this.url = url;
        this.protocols = protocols;
        this.socket = null;
        this.onOpen = null;
        this.onMessage = null;
        this.onClose = null;
        this.onError = null;
    }

    connect() {
        this.socket = this.protocols
            ? new WebSocket(this.url, this.protocols)
            : new WebSocket(this.url);

        this.socket.onopen = (event) => {
            if (this.onOpen) {
                this.onOpen(event);
            }
        };

        this.socket.onmessage = (event) => {
            if (this.onMessage) {
                this.onMessage(event);
            }
        };

        this.socket.onclose = (event) => {
            if (this.onClose) {
                this.onClose(event);
            }
        };

        this.socket.onerror = (error) => {
            if (this.onError) {
                this.onError(error);
            }
        };
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(data);
        } else {
            console.error('WebSocket is not connected.');
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}
