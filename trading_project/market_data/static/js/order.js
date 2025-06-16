document.querySelectorAll('.symbol-cell').forEach(cell => {
    cell.addEventListener('click', function() {
        const symbol = this.textContent.trim();  // Get the symbol from the clicked cell
        const symbolInput = document.getElementById('punch_order_symbol');  // ✅ use this ID
        symbolInput.value = symbol;  // Set the input box value
        console.log(`✅ Symbol "${symbol}" set in Punch Order form.`);
    });
});


// get percentage input for target and stop loss based on required condition 
function toggleTargetStopInputs() {
    const useSame = document.getElementById("useSamePercent").checked;

    // Toggle visibility
    document.getElementById("percentInputGroup").classList.toggle("d-none", !useSame);
    document.getElementById("separatePercentInputs").classList.toggle("d-none", useSame);
}

// Call on page load
document.addEventListener("DOMContentLoaded", toggleTargetStopInputs);
function getTargetAndStop(entry) {
    const useSame = document.getElementById("useSamePercent").checked;

    if (useSame) {
        const percent = parseFloat(document.getElementById("percent").value) || 3;
        const upper = +(entry * (1 + percent / 100)).toFixed(2);
        const lower = +(entry * (1 - percent / 100)).toFixed(2);
        return { upper, lower };
    } else {
        const targetPercent = parseFloat(document.getElementById("target-percent").value) || 3;
        const stoplossPercent = parseFloat(document.getElementById("stoploss-percent").value) || 3;
        const upper = +(entry * (1 + targetPercent / 100)).toFixed(2);
        const lower = +(entry * (1 - stoplossPercent / 100)).toFixed(2);
        return { upper, lower };
    }
}





// 🔁 Keeps latest LTP for each token
window.latestLtpByToken = {};

window.addEventListener("marketDataUpdated", (e) => {
    const tick = e.detail;
    const token = String(tick.token);
    const ltp = +(tick.last_traded_price / 100).toFixed(2);
    window.latestLtpByToken[token] = ltp;

    // console.log("📡 Tick Update:", token, "LTP ₹" + ltp);
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
        transactiontype: "BUY"
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
            order_id = data.response.data.orderid;
            alert("✅ Order placed successfully! Order ID: " + order_id);
            const get_order_book = await fetch('/get-order-book');
            const order_book = await get_order_book.json();
            // await fetchOrderBook();

            const intervalId = setInterval(async () => {
                console.log("🔄 Polling order book for order ID:", order_id);
                
                try {
                    const res = await fetch("/get-order-book");
                    console.log("📡 Fetched order book response:", res);
            
                    const result = await res.json();
                    console.log("📄 Parsed order book data:", result);
            
                    if (result && result.data && Array.isArray(result.data)) {
                        const matchedOrder = result.data.find(order =>
                            order.orderid === order_id
                        );
                        console.log("✅ Matched Order Found:", matchedOrder);
                        if (matchedOrder) {
                            const status = matchedOrder.status.toLowerCase();
                            const filled = (parseInt(matchedOrder.filledshares))/75;
                            const avgPrice = parseFloat(matchedOrder.averageprice);
                            const txnType = matchedOrder.transactiontype;
            
                            if (status === "trigger pending") {
                                console.log("⏳ Order is still in trigger pending state. Retrying...");
                                return;
                            }
            
                            if (status === "cancelled" || status === "rejected" || status === "AMO")  {
                                console.warn(`❌ Order has been ${status}. Stopping polling.`);
                                clearInterval(intervalId);
                                alert(`❌ Order was ${status}.`);
                                return;
                            }
                            if (status === "complete" && filled > 0 && avgPrice > 0 && txnType === "BUY") {
                                clearInterval(intervalId);
                                const symboltoken = matchedOrder.symboltoken;
                                const tradingsymbol = matchedOrder.tradingsymbol;

                                // ✅ Advanced Exit Logic Start
                                const entry = avgPrice;
                                let currentQty = filled;
                                let sl = entry * 0.97;
                                let targetReached = 0;
                                const step = 0.03; // 3%
                                let stepTarget = entry * (1 + step);

                                
                                console.log(`🚀 Buy completed. Tracking ${token} | Entry ₹${entry} | Target ₹${stepTarget} | Stop ₹${sl}`);

                                const trackInterval = setInterval(async() => {
                                    const ltp = window.latestLtpByToken[symboltoken];
                                    if (!ltp) return;

                                    // Stoploss check
                                    if (ltp <= sl) {
                                        sendSell(tradingsymbol, symboltoken, currentQty, ltp);
                                        clearInterval(trackInterval);
                                        console.log(`⛔ STOPLOSS HIT: ₹${ltp}`);
                                    }

                                    // Target logic
                                    if (ltp >= stepTarget) {
                                        if (filled === 1) {
                                            sendSell(tradingsymbol, symboltoken, 1, ltp);
                                            clearInterval(trackInterval);
                                            console.log(`🎯 3% Target hit (single lot)`);
                                        } else if (filled === 2 && targetReached === 0) {
                                            sendSell(tradingsymbol, symboltoken, 1, ltp);
                                            currentQty = 1;
                                            sl = entry;
                                            targetReached++;
                                            stepTarget = stepTarget * (1 + step);
                                            console.log(`✅ 1 lot booked at 3%, SL moved to cost.`);
                                        } else if (filled > 2 && targetReached === 0) {
                                            const exitQty = Math.ceil(filled * 0.75);
                                            sendSell(tradingsymbol, symboltoken, exitQty, ltp);
                                            currentQty -= exitQty;
                                            sl = entry;
                                            targetReached++;
                                            stepTarget = stepTarget * (1 + step);
                                            console.log(`✅ 75% booked, SL moved to cost.`);
                                        } else {
                                            // Continue trailing
                                            sl = entry * (1 + step * targetReached);
                                            targetReached++;
                                            stepTarget = stepTarget * (1 + step);
                                            console.log(`📈 Trailing SL moved up to ₹${sl}`);
                                        }
                                    }
                                }, 350);
                            // if (status === "complete" && filled > 0 && avgPrice > 0 && txnType === "BUY") 
                            // {
                            //     clearInterval(intervalId);
                                
                            //     // 🎯 Real-time +/-3% Tracker
                            //     const entry = avgPrice;
                            //     const { upper, lower } = getTargetAndStop(entry);
                            //     const token = String(symboltoken);

                            //     console.log(`🚀 Buy completed. Tracking ${token} | Entry ₹${entry} | Target ₹${upper} | Stop ₹${lower}`);
                            //     console.log("🎯 Order fully executed. Preparing to place SELL order...");

                            //     const watchId = setInterval(async () => {
                            //         const ltp = window.latestLtpByToken[token];
                            //         if (!ltp) return;

                            //         if (ltp >= upper) {
                            //             clearInterval(watchId);
                            //             sendSell(tradingsymbol ,token, filled, ltp);
                            //             console.log(`🎯 +${upper}% TARGET hit for ${token} at ₹${ltp}`);
                                        
                            //         } else if (ltp <= lower) {
                            //             clearInterval(watchId);
                            //             sendSell(tradingsymbol, token, filled, ltp);
                            //             console.log(`⛔ -${lower}"% STOPLOSS hit for ${token} at ₹${ltp}`);
                            //         }
                            //     }, 350);
                            }
                        } else {
                            console.log("🔍 No order found with ID:", buyOrderId);
                        }
                    } else {
                        console.error("❗ Invalid response format or empty order book.");
                    }
                } catch (err) {
                    console.error("❌ Error while polling order status:", err);
                }
            }, 1000); // Poll every 1 second

        } else {
            alert("❌ Order failed: " + data.message);
        }
    } catch (error) {
        console.error("❌ Error placing order:", error);
        alert("⚠️ An error occurred. Check console.");
    }


}


async function sendSell(symbol ,token, qty, price) {
    const sellOrderData = {
        tradingsymbol: symbol,
        symboltoken: token,
        order_type: "MARKET",  
        quantity: qty,
        triggerprice: price,
        transactiontype: "SELL",
        
    };

    console.log("📤 Placing SELL order:", sellOrderData);
    try {
        const response = await fetch("/place-order/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify(sellOrderData)
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


async function placeSellOrder() {
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
        transactiontype: "SELL"
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
        const entryPrice = (triggerPrice + 0.2).toFixed(2);
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
                        <td>${order.updatetime}</td>
                        <td>${order.orderid}</td>
                        <td>${order.tradingsymbol}</td>
                        <td>${order.ordertype}</td>
                        <td class="${order.orderstatus.toLowerCase() === 'rejected' ? 'text-danger' : order.orderstatus.toLowerCase() === 'complete' ? 'text-success' : 'text-warning'}">
                            ${order.orderstatus}
                        </td>
                        <td>${order.quantity}</td>
                        <td>${order.filledshares}</td>
                        <td>${order.averageprice}</td>
                        <td>${order.transactiontype}</td>
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
                        <td>${trade.strikeprice}</td>
                        <td>${trade.tradevalue}</td>
                        <td>${trade.transactiontype}</td>
                        <td>${trade.marketlot}</td>
                        <td>${trade.fillid}</td>
                        <td>${trade.filltime}</td>
                        <td>${trade.fillprice}</td>
                        <td>${trade.fillsize}</td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        } else {
            tableBody.innerHTML = `<tr><td colspan="10" class="text-center">No trades found</td></tr>`;
        }

    } catch (error) {
        console.error("❌ Error fetching trade book:", error);
    }
}



async function handlePostSellOrder(orderId, symbol, qty) {
    console.log("⏳ Checking order status for:", orderId);

    let statusResp = await fetch(`/get-order-status/${orderId}`);
    let statusData = await statusResp.json();

    if (statusData.status === "success" && statusData.data.order_status === "complete") {
        console.log("✅ Sell order completed. Checking open positions...");

        let posResp = await fetch('/get-open-positions');
        let posData = await posResp.json();

        let position = posData.data.find(pos => pos.tradingsymbol === symbol);
        if (position) {
            let entryPrice = parseFloat(position.average_price);
            let targetPrice = entryPrice * 0.103;  // +3%
            console.log(`🎯 Targeting additional sell at: ${targetPrice}`);

            // Retry placing sell at target price
            const targetOrderData = {
                tradingsymbol: symbol,
                symboltoken: getTokenBySymbol(symbol),
                order_type: "LIMIT",
                quantity: qty,
                price: targetPrice,
                transactiontype: "SELL"
            };

            const retryResp = await fetch("/place-order/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify(targetOrderData)
            });

            const retryData = await retryResp.json();
            if (retryData.status === "success") {
                console.log("✅ Retry sell order placed at target price.");
            } else {
                console.log("❌ Retry sell order failed. Will check position and retry...");
                await handlePostSellOrder(orderId, symbol, qty);  // Recursive retry
            }
        } else {
            console.log("✅ Position closed successfully.");
        }
    } else {
        console.log("❌ Sell order incomplete or failed.");
    }
}

