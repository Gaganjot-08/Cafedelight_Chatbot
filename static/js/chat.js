const chatWindow = document.getElementById("chat-window");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

let typingIndicatorRow = null;

function timeNow() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(str) {
    if (typeof str !== "string") return str;
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Smooth auto-scroll that glides gracefully without fighting CSS entrance transforms.
 */
function scrollToBottom(smooth = true) {
    requestAnimationFrame(() => {
        if (smooth && typeof chatWindow.scrollTo === "function") {
            chatWindow.scrollTo({
                top: chatWindow.scrollHeight,
                behavior: "smooth"
            });
        } else {
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    });
}

function showTypingIndicator() {
    if (typingIndicatorRow) return;

    typingIndicatorRow = document.createElement("div");
    typingIndicatorRow.className = "bubble-row bot typing-indicator-row";

    const bubble = document.createElement("div");
    bubble.className = "bubble bot typing-bubble";

    const name = document.createElement("div");
    name.className = "bubble-name";
    name.textContent = "Cafe Delight";

    const dots = document.createElement("div");
    dots.className = "typing-dots";
    dots.setAttribute("aria-label", "Bot is typing");
    dots.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';

    bubble.appendChild(name);
    bubble.appendChild(dots);
    typingIndicatorRow.appendChild(bubble);
    chatWindow.appendChild(typingIndicatorRow);
    scrollToBottom(true);
}

function hideTypingIndicator() {
    if (typingIndicatorRow) {
        typingIndicatorRow.remove();
        typingIndicatorRow = null;
    }
}

/**
 * Contextual option extraction from bot message text.
 * Provides interactive action buttons for checkout flow, order types, etc.
 */
function extractOptionsFromMessage(text) {
    if (!text || typeof text !== "string") return null;
    const lower = text.toLowerCase();

    // Final order confirmation prompt
    if (lower.includes("'confirm'") && lower.includes("'cancel'")) {
        return [
            { label: "✓ Confirm Order", value: "confirm" },
            { label: "✕ Cancel", value: "cancel" }
        ];
    }

    // Order type selection prompt
    if (lower.includes("dine-in") && lower.includes("takeaway") && lower.includes("delivery")) {
        return [
            { label: "🍽️ Dine-in", value: "Dine-in" },
            { label: "🥡 Takeaway", value: "Takeaway" },
            { label: "🚗 Delivery", value: "Delivery" }
        ];
    }

    // Prompt indicating ready to checkout
    if (lower.includes("say 'checkout'")) {
        return [
            { label: "🛒 Checkout Now", value: "checkout" }
        ];
    }

    // Empty cart menu prompt
    if (lower.includes("would you like to see our menu?")) {
        return [
            { label: "📜 View Menu", value: "show menu" }
        ];
    }

    return null;
}


function addBubble(text, sender, options = null) {
    const row = document.createElement("div");
    row.className = `bubble-row ${sender}`;

    const bubble = document.createElement("div");
    bubble.className = `bubble ${sender}`;

    const name = document.createElement("div");
    name.className = "bubble-name";
    name.textContent = sender === "bot" ? "Cafe Delight" : "You";

    const msg = document.createElement("div");
    msg.className = "bubble-text";
    msg.textContent = text;

    const time = document.createElement("div");
    time.className = "bubble-time";
    time.textContent = timeNow();

    bubble.appendChild(name);
    bubble.appendChild(msg);

    // Contextual interactive buttons (option-btn, confirm-btn, cancel-btn)
    if (!options && sender === "bot") {
        options = extractOptionsFromMessage(text);
    }

    if (options && options.length) {
        const btnContainer = document.createElement("div");
        btnContainer.className = "options-container";
        options.forEach(opt => {
            const btn = document.createElement("button");
            const valLow = (opt.value || "").toLowerCase();
            let btnClass = "option-btn";
            if (valLow === "confirm") btnClass += " confirm-btn";
            else if (valLow === "cancel") btnClass += " cancel-btn";

            btn.className = btnClass;
            btn.type = "button";
            btn.textContent = opt.label;
            btn.onclick = () => {
                btnContainer.querySelectorAll("button").forEach(b => b.disabled = true);
                sendToChat(opt.value);
            };
            btnContainer.appendChild(btn);
        });
        bubble.appendChild(btnContainer);
    }

    bubble.appendChild(time);
    row.appendChild(bubble);
    chatWindow.appendChild(row);
    scrollToBottom(true);
}

function updateCartSidebar(cart) {
    const linesDiv = document.getElementById("cart-lines");
    const itemCount = document.getElementById("item-count");
    const totalAmount = document.getElementById("total-amount");

    // Retrigger subtle pulse animation on cart values
    if (itemCount && totalAmount) {
        itemCount.classList.remove("cart-value-pulse");
        totalAmount.classList.remove("cart-value-pulse");
        void itemCount.offsetWidth; // Force reflow
        itemCount.classList.add("cart-value-pulse");
        totalAmount.classList.add("cart-value-pulse");
    }

    if (!cart || !cart.lines || !cart.lines.length) {
        linesDiv.innerHTML = '<div class="cart-empty-message">Your cart is empty.<br><br>Add something delicious<br>to get started.</div>';
        itemCount.textContent = "0 items";
        totalAmount.textContent = "Rs. 0";
        return;
    }

    let html = "";
    cart.lines.forEach(l => {
        html += `<div class="cart-item-row"><div class="cart-item-meta"><span class="cart-item-qty">${l.quantity}×</span> <span class="cart-item-name">${escapeHtml(l.item)}</span></div><span class="cart-item-price">Rs. ${l.amount}</span></div>`;
    });
    linesDiv.innerHTML = html;
    itemCount.textContent = `${cart.total_items} ${cart.total_items === 1 ? 'item' : 'items'}`;
    totalAmount.textContent = `Rs. ${cart.total}`;
}

async function sendToChat(text, showUserBubble = true) {
    if (showUserBubble) addBubble(text, "user");
    showTypingIndicator();
    sendBtn.disabled = true;

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        hideTypingIndicator();
        if (data.message) {
            // Subtle 90ms micro-beat gives an organic "bot finished thinking" transition
            setTimeout(() => {
                addBubble(data.message, "bot", data.options);
            }, 90);
        }
        updateCartSidebar(data.cart);
    } catch (err) {
        hideTypingIndicator();
        console.error("Chat request failed:", err);
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
}

sendBtn.onclick = () => {
    const text = userInput.value.trim();
    if (!text) return;
    userInput.value = "";

    // Trigger launching micro-motion on send button
    sendBtn.classList.add("btn-launching");
    setTimeout(() => sendBtn.classList.remove("btn-launching"), 360);

    sendToChat(text);
};

userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        sendBtn.click();
    }
});

document.getElementById("btn-menu").onclick = () => sendToChat("show menu");
document.getElementById("btn-order").onclick = () => sendToChat("I want to order");

document.getElementById("btn-cart").onclick = async () => {
    showTypingIndicator();
    try {
        const res = await fetch("/api/cart/view", { method: "POST" });
        const data = await res.json();
        hideTypingIndicator();
        setTimeout(() => {
            addBubble(data.message, "bot");
        }, 90);
        updateCartSidebar(data.cart);
    } catch (err) {
        hideTypingIndicator();
        console.error("Cart view failed:", err);
    }
};

document.getElementById("btn-clear").onclick = async () => {
    if (!confirm("Are you sure you want to clear your current order?")) return;
    showTypingIndicator();
    try {
        const res = await fetch("/api/cart/clear", { method: "POST" });
        const data = await res.json();
        hideTypingIndicator();
        setTimeout(() => {
            addBubble(data.message, "bot");
        }, 90);
        updateCartSidebar(data.cart);
    } catch (err) {
        hideTypingIndicator();
        console.error("Cart clear failed:", err);
    }
};

window.onload = () => {
    addBubble(
        "Welcome to Cafe Delight!\n\n" +
        "I am your personal ordering assistant. I can help you explore our menu, check prices, " +
        "describe dishes and place your order.\n\n" +
        "What would you like to have today?",
        "bot"
    );
};