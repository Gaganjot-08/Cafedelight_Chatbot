const chatWindow = document.getElementById("chat-window");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

function timeNow() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function addBubble(text, sender) {
    const row = document.createElement("div");
    row.className = `bubble-row ${sender}`;

    const bubble = document.createElement("div");
    bubble.className = `bubble ${sender}`;

    const name = document.createElement("div");
    name.className = "bubble-name";
    name.textContent = sender === "bot" ? "Cafe Delight" : "You";

    const msg = document.createElement("div");
    msg.textContent = text;

    const time = document.createElement("div");
    time.className = "bubble-time";
    time.textContent = timeNow();

    bubble.appendChild(name);
    bubble.appendChild(msg);
    bubble.appendChild(time);
    row.appendChild(bubble);
    chatWindow.appendChild(row);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function updateCartSidebar(cart) {
    const linesDiv = document.getElementById("cart-lines");
    const itemCount = document.getElementById("item-count");
    const totalAmount = document.getElementById("total-amount");

    if (!cart.lines.length) {
        linesDiv.innerHTML = "Your cart is empty.<br><br>Add something delicious<br>to get started.";
        itemCount.textContent = "0 items";
        totalAmount.textContent = "Rs. 0";
        return;
    }

    let text = "";
    cart.lines.forEach(l => {
        text += `${l.quantity} x ${l.item}\nRs. ${l.amount}\n\n`;
    });
    linesDiv.textContent = text.trim();
    itemCount.textContent = `${cart.total_items} items`;
    totalAmount.textContent = `Rs. ${cart.total}`;
}

async function sendToChat(text, showUserBubble = true) {
    if (showUserBubble) addBubble(text, "user");

    const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    if (data.message) addBubble(data.message, "bot");
    updateCartSidebar(data.cart);
}

sendBtn.onclick = () => {
    const text = userInput.value.trim();
    if (!text) return;
    userInput.value = "";
    sendToChat(text);
};

userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendBtn.click();
});

document.getElementById("btn-menu").onclick = () => sendToChat("show menu");
document.getElementById("btn-order").onclick = () => sendToChat("I want to order");

document.getElementById("btn-cart").onclick = async () => {
    const res = await fetch("/api/cart/view", { method: "POST" });
    const data = await res.json();
    addBubble(data.message, "bot");
    updateCartSidebar(data.cart);
};

document.getElementById("btn-clear").onclick = async () => {
    if (!confirm("Are you sure you want to clear your current order?")) return;
    const res = await fetch("/api/cart/clear", { method: "POST" });
    const data = await res.json();
    addBubble(data.message, "bot");
    updateCartSidebar(data.cart);
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