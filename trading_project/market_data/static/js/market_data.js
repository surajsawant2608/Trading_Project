// Select the form and input field
const subscribeForm = document.querySelector(".subscribe");
const subscribeInput = document.querySelector("#subscribe-input");
const unsubscribeForm = document.querySelector(".unsubscribe");
const unsubscribeInput = document.querySelector("#unsubscribe-input");
const socket = new WebSocket("ws://localhost:8000/ws/market_data/");
const tokenRows = {};
const symbolInput = document.getElementById('punch_order_symbol');
const tableBody = document.getElementById("market_data");
const optionChainContainer = document.getElementById("option_chain_data");
window.tokenSymbolMap = {};


// Subscribe function
function subscribeTokens(tokens) {
    const data = JSON.stringify({ action: "subscribe", tokens });
    console.log("Subscribing:", data);
    socket.send(data);
}

document.addEventListener("DOMContentLoaded", async function () {
    try {
        const res = await fetch("/orders/start-order-ws/");
        const data = await res.json();
        console.log("📡 Order WebSocket started:", data);
    } catch (error) {
        console.error("❌ Failed to start Order WebSocket:", error);
    }
});

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
        const response = await fetch("/static/OpenAPIScripMaster020226.json");
        const data = await response.json();
        data.forEach(item => {
            tokenSymbolMap[String(item.token)] = item.symbol;
        });
        console.log("✅ Token-Symbol Mapping Loaded:", tokenSymbolMap);
    } catch (error) {
        console.error("❌ Error loading token mapping:", error);
    }
}

loadTokenMappings();

// Add event delegation: listen for clicks on symbol cells
tableBody.addEventListener('click', function(event) {
    const target = event.target;
    if (target.classList.contains('symbol-cell')) {
        const symbol = target.textContent.trim();
        symbolInput.value = symbol;
        console.log(`✅ Symbol "${symbol}" set in Punch Order form.`);
    }
});


socket.onopen = function () {
    console.log("✅ Connected to WebSocket");
};

socket.onmessage = function (event) {
    try {
        const parsedData = JSON.parse(event.data);
        const marketData = parsedData.data || parsedData;

        window.latestMarketData = marketData;
        const customEvent = new CustomEvent("marketDataUpdated", { detail: marketData });
        window.dispatchEvent(customEvent);

        const token = marketData.token;
        const symbol = tokenSymbolMap[String(token)] || "Unknown";
        
        // Remove "Waiting for updates..." row if it exists
        const waitingRow = tableBody.querySelector("td[colspan]");
        if (waitingRow && waitingRow.textContent.includes("Waiting for updates")) {
            tableBody.removeChild(waitingRow.parentElement);
        }

        // Handle unsubscribe confirmation
        if (parsedData.action === "unsubscribe_confirmation") {
            console.log(`✅ Confirmed Unsubscribed: ${parsedData.tokens}`);
            parsedData.tokens.forEach(token => {
                const row = document.getElementById(`token-${token}`);
                if (row) {
                    row.remove();
                    console.log(`❌ Removed token ${token} from UI`);
                }
                delete tokenRows[token];
                delete tokenSymbolMap[token];
            });
            return;
        }

        // Create or update table row
        let row = document.getElementById(`token-${token}`);
        const ltp = (marketData.last_traded_price / 100).toFixed(2)
        if (!row) {
            row = document.createElement("tr");
            row.id = `token-${token}`;
            row.innerHTML = `
                <td>${token}</td>
                <td class="symbol-cell" style="cursor: pointer;" id="symbol-${token}">${symbol}</td>
                <td class="ltp text-success fw-bold" id="ltp-${token}">
                    ${ltp}
                </td>
            `;
            tableBody.appendChild(row);
            tokenRows[token] = row;
        } else {
            row.querySelector(`#ltp-${token}`).innerText = (marketData.last_traded_price / 100).toFixed(2);
            const symbolCell = row.querySelector(`#symbol-${token}`);
            if (symbolCell.innerText === "Unknown") {
                symbolCell.innerText = symbol;
            }
        }

    } catch (error) {
        console.error("❌ Error parsing JSON:", error);
    }
};

socket.onclose = function () {
    console.log("❌ WebSocket Disconnected");
};

socket.onerror = function (error) {
    console.error("❌ WebSocket Error:", error);
};



