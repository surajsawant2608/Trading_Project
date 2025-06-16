document.querySelectorAll('.symbol-cell').forEach(cell => {
    cell.addEventListener('click', function() {
        const symbol = this.textContent.trim();  // Get the symbol from the clicked cell
        const symbolInput = document.getElementById('punch_order_symbol');  // ✅ use this ID
        symbolInput.value = symbol;  // Set the input box value
        console.log(`✅ Symbol "${symbol}" set in Punch Order form.`);
    });
});

async function placeBuyOrder() {
    let token = null;
    const symbol = document.getElementById("punch_order_symbol").value.trim();
    const qty = document.getElementById("lots").value.trim();
    const triggerPrice = parseFloat(document.getElementById("triggerPrice").value.trim());
    const price = document.getElementById("entryPrice").textContent.trim();;
    
    const orderTypeElement = document.getElementById("orderType");
    if (!orderTypeElement || !orderTypeElement.value) {
        alert("❗ Order type is not selected.");
        return;
    }
    const orderType = orderTypeElement.value.toUpperCase();

    // Try to find token by symbol
    if (symbol) {
        token = getTokenBySymbol(symbol);
    }

    // Validation
    if (!token || !symbol || !qty || (orderType === "LIMIT" && !price)) {
        alert("❗ Please fill in all required fields.");
        return;
    }

    const orderData = {
        
        tradingsymbol: symbol,
        symboltoken: token,
        order_type: orderType,
        quantity: qty,
        price: price,
        triggerprice: triggerPrice,
    };
    console.log("📦 Order Data being sent:", orderData);

    try {
        const response = await fetch("/place-order/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify(orderData)
        });

        const data = await response.json();
        if (data.status === "success") {
            alert("✅ Order placed successfully!");
        } else {
            alert("❌ Order failed: " + data.message);
        }
    } catch (error) {
        console.error("❌ Error placing order:", error);
        alert("⚠️ An error occurred. Check console.");
    }
}
function updateEntryPrice() {
    const triggerPrice = parseFloat(document.getElementById("triggerPrice").value.trim());

    if (!isNaN(triggerPrice)) {
        const entryPrice = (triggerPrice + 0.5).toFixed(2);
        document.getElementById("entryPrice").textContent = entryPrice;
    } else {
        document.getElementById("entryPrice").textContent = "--";
    }
}

// Helper to get token by symbol
function getTokenBySymbol(symbol) {
    const tokenMap = window.tokenSymbolMap || {};
    for (const [token, mappedSymbol] of Object.entries(tokenMap)) {
        if (mappedSymbol.toUpperCase() === symbol.toUpperCase()) {
            return token;
        }
    }
    console.warn("⚠️ Symbol not found in token map:", symbol);
    return null;
}

// CSRF token helper
function getCSRFToken() {
    let cookieValue = null;
    const name = "csrftoken";
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


// Fecth order book code
async function fetchOrderBook() {
    try {
        const response = await fetch('/get-order-book');
        const data = await response.json();

        console.log("📘 Order Book:", data); // Debugging output

        const tableBody = document.getElementById('orderBookTable');
        tableBody.innerHTML = ""; // Clear previous rows

        if (data.status && Array.isArray(data.data) && data.data.length > 0) {
            data.data.forEach(order => {
                const row = `
                    <tr>
                        <td>${order.orderid}</td>
                        <td>${order.tradingsymbol}</td>
                        <td>${order.ordertype}</td>
                        <td class="${order.orderstatus.toLowerCase() === 'rejected' ? 'text-danger' : ''}">
                            ${order.orderstatus}
                        </td>
                        <td>${order.quantity}</td>
                        <td>${order.filledshares}</td>
                        <td>${order.price}</td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        } else {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center">No orders found</td></tr>`;
        }

    } catch (error) {
        console.error("❌ Error fetching order book:", error);
    }
}

// fetch trade book
async function fetchTradeBook() {
    try {
        const response = await fetch('/get-trade-book');
        const data = await response.json();

        console.log("📘 Trade Book:", data); // Debugging output

        const tableBody = document.getElementById('tradeBookTable');
        tableBody.innerHTML = ""; // Clear previous rows

        if (data.status && data.data && Array.isArray(data.data) && data.data.length > 0) {
            data.data.forEach(trade => {
                const row = `
                    <tr>
                        <td>${trade.orderid}</td>
                        <td>${trade.tradingsymbol}</td>
                        <td>${trade.transactiontype}</td>
                        <td>${trade.exchange}</td>
                        <td>${trade.tradedqty}</td>
                        <td>${trade.tradedprice}</td>
                        <td>${trade.tradevalue}</td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        } else {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center">No trades found</td></tr>`;
        }

    } catch (error) {
        console.error("❌ Error fetching trade book:", error);
    }
}


