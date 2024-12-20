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

    const botMessage = document.createElement("div");
    botMessage.classList.add("message", "bot");
    chatWindow.appendChild(botMessage);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    const api = localStorage.getItem('apiUrl') || '';
    const model = localStorage.getItem('modelName') || '';

    try {
        const response = await fetch("/handle-prompt/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `user_prompt=${encodeURIComponent(inputValue)}&api_url=${encodeURIComponent(api)}&model_name=${encodeURIComponent(model)}`,
        });

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        // Initially set to empty
        botMessage.innerHTML = "";

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let isFirstChunk = true;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            if (value) {
                const chunk = decoder.decode(value, { stream: true });
                if (isFirstChunk) {
                    // The first chunk might be "Thinking..."
                    // Clear the bot message and then append
                    botMessage.innerHTML = "";
                    isFirstChunk = false;
                }
                // Append the chunk in a span for proper alignment
                botMessage.innerHTML += `<span>${chunk}</span>`;
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }
        }

        botMessage.innerHTML += "<br><span class='response-complete'>Response complete.</span>";
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

// Model/API selection logic
let modelHistory = JSON.parse(localStorage.getItem('modelHistory')) || [];
// modelHistory will store objects: { modelName: string, apiUrl: string }

const changeModelButton = document.getElementById('change-model');
const modelModal = document.getElementById('model-modal');
const closeModelButton = document.getElementById('close-modal');
const saveModelSettingsButton = document.getElementById('save-model-settings');
const modelHistoryList = document.getElementById('model-history');

// Popular models
const popularModels = [
    { modelName: 'gpt-4o', hint: 'Enter API URL manually after selecting this.' },
    { modelName: 'o1', hint: 'Enter API URL manually after selecting this.' }
];

function updateModelHistoryList() {
    modelHistoryList.innerHTML = '';
    // Show last 3 used models
    modelHistory.slice(-3).forEach(m => {
        const li = document.createElement('li');
        const btn = document.createElement('button');
        btn.innerText = `${m.modelName} (${m.apiUrl})`;
        btn.classList.add('action-button');
        btn.onclick = () => {
            document.getElementById('model-input').value = m.modelName;
            document.getElementById('api-input').value = m.apiUrl;
        };
        li.appendChild(btn);
        modelHistoryList.appendChild(li);
    });

    // Add a section for popular models
    const popularHeader = document.createElement('p');
    popularHeader.innerText = 'Popular Models:';
    modelHistoryList.appendChild(popularHeader);

    popularModels.forEach(pm => {
        const li = document.createElement('li');
        const btn = document.createElement('button');
        btn.innerText = pm.modelName;
        btn.classList.add('action-button');
        btn.onclick = () => {
            document.getElementById('model-input').value = pm.modelName;
            // User can input API URL manually
            // Show a hint?
            alert(`Selected ${pm.modelName}. Please enter the API URL manually before saving.`);
        };
        li.appendChild(btn);
        modelHistoryList.appendChild(li);
    });
}

changeModelButton.addEventListener('click', () => {
    updateModelHistoryList();
    modelModal.style.display = 'flex';
});

closeModelButton.addEventListener('click', () => {
    modelModal.style.display = 'none';
});

saveModelSettingsButton.addEventListener('click', () => {
    const apiInput = document.getElementById('api-input').value.trim();
    const modelInput = document.getElementById('model-input').value.trim();
    if (apiInput && modelInput) {
        localStorage.setItem('apiUrl', apiInput);
        localStorage.setItem('modelName', modelInput);

        const existing = modelHistory.find(m => m.modelName === modelInput && m.apiUrl === apiInput);
        if (!existing) {
            modelHistory.push({ modelName: modelInput, apiUrl: apiInput });
            localStorage.setItem('modelHistory', JSON.stringify(modelHistory));
        }

        modelModal.style.display = 'none';
        alert('Model & API updated successfully!');
    } else {
        alert('Please enter both API and Model');
    }
});