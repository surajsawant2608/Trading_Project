const socket = new WebSocket("ws://127.0.0.1:8000/ws/market_data/");

socket.onopen = function () {
    console.log("WebSocket connection established");
}
socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log("Message received:", data);
};

socket.onclose = function (event) {
    console.log("WebSocket connection closed:", event);
};
