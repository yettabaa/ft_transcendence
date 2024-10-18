// websocket.ts
class WebSocketSingleton {
    private static instance: WebSocket | null = null;

    static getInstance(url: string): WebSocket {
        if (!this.instance) {
            this.instance = new WebSocket(url);
            this.instance.onopen = () => {
                console.log('WebSocket connection established');
            };
            this.instance.onmessage = (event) => {
                console.log('Message from server:', event.data);
                // You may want to handle incoming messages here
            };
            this.instance.onclose = (event) => {
                console.log('WebSocket connection closed:', event);
            };
            this.instance.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
        return this.instance;
    }
}

export default WebSocketSingleton;
