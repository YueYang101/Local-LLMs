const DEBUG_MODE = true;

function resetInputHeight() {
    const userInput = document.getElementById("user-input");
    userInput.style.height = `${initialHeight}px`;
}

function copyToClipboard(content) {
    navigator.clipboard.writeText(content)
        .then(() => {
            if (DEBUG_MODE) console.debug("Copied to clipboard!");
        })
        .catch((err) => {
            console.error("Failed to copy to clipboard:", err);
        });
}

document.getElementById("chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const userInput = document.getElementById("user-input");
    const chatWindow = document.getElementById("chat-window");

    const inputValue = userInput.value.trim();
    if (!inputValue) return;

    userInput.value = "";

    const userMessage = document.createElement("div");
    userMessage.classList.add("message", "user");
    userMessage.innerText = inputValue;

    const userActions = document.createElement("div");
    userActions.classList.add("message-actions");

    const copyButton = document.createElement("button");
    copyButton.innerText = "Copy";
    copyButton.classList.add("action-button");
    copyButton.onclick = () => copyToClipboard(inputValue);

    const reInputButton = document.createElement("button");
    reInputButton.innerText = "Re-input";
    reInputButton.classList.add("action-button");
    reInputButton.onclick = () => {
        userInput.value = inputValue;
        resetInputHeight();
    };

    userActions.appendChild(copyButton);
    userActions.appendChild(reInputButton);
    userMessage.appendChild(userActions);

    userMessage.addEventListener("mouseenter", () => {
        userActions.style.display = "flex";
    });
    userMessage.addEventListener("mouseleave", () => {
        userActions.style.display = "none";
    });
    userActions.style.display = "none";

    chatWindow.appendChild(userMessage);

    // Create a container for the bot's response
    const botMessage = document.createElement("div");
    botMessage.classList.add("message", "bot");
    chatWindow.appendChild(botMessage);

    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch("/handle-prompt/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `user_prompt=${encodeURIComponent(inputValue)}`,
        });

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        // Stream the response word by word
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            if (value) {
                const chunk = decoder.decode(value, { stream: true });
                botMessage.innerHTML += chunk; // Append each word chunk to the message
                chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to the bottom
            }
        }
    } catch (error) {
        console.error("Error during fetch:", error);

        const errorMessage = document.createElement("div");
        errorMessage.classList.add("message", "bot");
        errorMessage.innerText = "Error: Unable to process your request.";
        chatWindow.appendChild(errorMessage);
    } finally {
        resetInputHeight();
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});

const userInput = document.getElementById("user-input");
const lineHeight = parseFloat(window.getComputedStyle(userInput).lineHeight);
const maxHeight = 200;
const initialHeight = userInput.scrollHeight;

userInput.style.height = `${initialHeight}px`;

userInput.addEventListener("input", () => {
    userInput.style.height = "auto";
    const newHeight = Math.min(userInput.scrollHeight, maxHeight);
    userInput.style.height = `${newHeight}px`;
});

userInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        if (!event.shiftKey) {
            event.preventDefault();
            document.getElementById("chat-form").dispatchEvent(new Event("submit"));
        }
    }
});

window.addEventListener("error", (event) => {
    if (DEBUG_MODE) console.error("Uncaught error:", event.message);
});