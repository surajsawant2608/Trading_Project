// Select the form and input field
const subscribeForm = document.querySelector(".subscribe");
const subscribeInput = document.querySelector("#subscribe-input");
const unsubscribeForm = document.querySelector(".unsubscribe");
const unsubscribeInput = document.querySelector("#unsubscribe-input");
const socket = new WebSocket("ws://localhost:8000/ws/market_data/");
const tokenRows = {};  
let tokenSymbolMap = {}; 

// Subscribe function
function subscribeTokens(tokens) {
    const data = JSON.stringify({ action: "subscribe", tokens });
    console.log("Subscribing:", data);
    socket.send(data);
}

// Unsubscribe function
function unsubscribeTokens(tokens) {
    const data = JSON.stringify({ action: "unsubscribe", tokens });
    console.log("Unsubscribing:", data);
    socket.send(data);
}

// Handle subscription form submission
subscribeForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const token = subscribeInput.value.trim();
    if (token) {
        subscribeTokens([token]);
        subscribeInput.value = "";
    } else {
        console.log("No token entered.");
    }
});

// Handle unsubscription form submission
unsubscribeForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const token = unsubscribeInput.value.trim();
    if (token) {
        unsubscribeTokens([token]);
        unsubscribeInput.value = "";
    } else {
        console.log("No token entered.");
    }
});

// Load token-symbol mappings
async function loadTokenMappings() {
    try {
        const response = await fetch("/static/OpenAPIScripMaster.json");
        const data = await response.json();
        data.forEach(item => {
            tokenSymbolMap[item.token] = item.symbol;
        });
        console.log("✅ Token-Symbol Mapping Loaded:", tokenSymbolMap);
    } catch (error) {
        console.error("❌ Error loading token mapping:", error);
    }
}

loadTokenMappings();

socket.onopen = function() {
    console.log("✅ Connected to WebSocket");
};

socket.onmessage = function(event) {
    try {
        // console.log("📩 Raw WebSocket Data:", event.data);
        const parsedData = JSON.parse(event.data);
        const marketData = parsedData.data || parsedData;
        const token = marketData.token;
        const symbol = tokenSymbolMap[token] || "Unknown";  
        const tableBody = document.getElementById("market_data");


        if (parsedData.action === "unsubscribe_confirmation") {
            console.log(`✅ Confirmed Unsubscribed: ${parsedData.tokens}`);

            parsedData.tokens.forEach(token => {
                const row = document.getElementById(`token-${token}`);
                if (row) {
                    row.remove();  // 🔥 Remove row from the table
                    console.log(`❌ Removed token ${token} from UI`);
                }
                // Clean up maps
                delete tokenRows[token];  
                delete tokenSymbolMap[token];
            });

            return;  // 🚀 Stop further processing for unsubscribe messages
        }


        if (tableBody.children.length === 1 && tableBody.firstChild.textContent.includes("Waiting")) {
            tableBody.innerHTML = "";
        }

        const exchangeTimestamp = new Date(marketData.exchange_timestamp);
        const currentTimestamp = new Date();
        const timeDifference = ((currentTimestamp - exchangeTimestamp) / 1000).toFixed(2);

        function formatTimestamp(date) {
            return date.toLocaleString("en-GB", { 
                year: "numeric", month: "2-digit", day: "2-digit", 
                hour: "2-digit", minute: "2-digit", second: "2-digit", 
                hour12: false 
            }).replace(",", "") + `:${date.getMilliseconds().toString().padStart(3, '0')}`;
        }

        const formattedExchangeTime = formatTimestamp(exchangeTimestamp);
        const formattedCurrentTime = formatTimestamp(currentTimestamp);

        let row = document.getElementById(`token-${token}`);
        if (!row) {
            row = document.createElement("tr");
            row.id = `token-${token}`;
            row.innerHTML = `
                <td>${token}</td>
                <td id="symbol-${token}">${symbol}</td>
                <td>${marketData.exchange_type}</td>
                <td class="ltp text-success fw-bold" id="ltp-${token}">${(marketData.last_traded_price / 100).toFixed(2)}</td>
                <td id="seq-${token}">${marketData.sequence_number}</td>
                <td id="exchange-time-${token}">${formattedExchangeTime}</td>
                <td id="current-time-${token}">${formattedCurrentTime}</td>
                <td id="time-diff-${token}">${timeDifference} sec</td>
                <td>${marketData.subscription_mode_val}</td>
            `;
            tableBody.appendChild(row);
            tokenRows[token] = row;  
        } else {
            row.querySelector(`#ltp-${token}`).innerText = (marketData.last_traded_price / 100).toFixed(2);
            row.querySelector(`#seq-${token}`).innerText = marketData.sequence_number;
            row.querySelector(`#exchange-time-${token}`).innerText = formattedExchangeTime;
            row.querySelector(`#current-time-${token}`).innerText = formattedCurrentTime;
            row.querySelector(`#time-diff-${token}`).innerText = `${timeDifference} sec`;

            const symbolCell = row.querySelector(`#symbol-${token}`);
            if (symbolCell.innerText === "Unknown") {
                symbolCell.innerText = symbol;
            }
        }
    } catch (error) {
        console.error("❌ Error parsing JSON:", error);
    }
};

socket.onclose = function() {
    console.log("❌ WebSocket Disconnected");
};

socket.onerror = function(error) {
    console.error("❌ WebSocket Error:", error);
};
