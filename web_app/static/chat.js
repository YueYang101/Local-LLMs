// ========================
// GLOBAL CONFIGURATION
// ========================
const DEBUG_MODE = true;

// ========================
// RESET INPUT HEIGHT FUNCTION
// ========================
function resetInputHeight() {
    const userInput = document.getElementById("user-input");
    userInput.style.height = `${initialHeight}px`; // Reset to the initial height
    if (DEBUG_MODE) console.debug("Input height reset to initial height.");
}

// ========================
// COPY TO CLIPBOARD FUNCTION
// ========================
function copyToClipboard(content) {
    navigator.clipboard.writeText(content)
        .then(() => {
            console.debug("Copied to clipboard!");
        })
        .catch((err) => {
            console.error("Failed to copy to clipboard:", err);
        });
}

// ========================
// FORM SUBMISSION EVENT HANDLER
// ========================
document.getElementById("chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const userInput = document.getElementById("user-input");
    const chatWindow = document.getElementById("chat-window");

    const inputValue = userInput.value.trim(); // Trim whitespace
    if (DEBUG_MODE) console.debug("Form submission detected. User input:", inputValue);

    if (!inputValue) {
        if (DEBUG_MODE) console.warn("No input provided. Skipping submission.");
        return;
    }

    userInput.value = "";
    if (DEBUG_MODE) console.debug("Input field cleared.");

    // Add user's message to chat window
    const userMessage = document.createElement("div");
    userMessage.classList.add("message", "user");
    userMessage.innerText = inputValue;

    // Create a container for hover actions (copy and re-input)
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

    // Add hover effect to show actions
    userMessage.addEventListener("mouseenter", () => {
        userActions.style.display = "flex"; // Show actions on hover
    });
    userMessage.addEventListener("mouseleave", () => {
        userActions.style.display = "none"; // Hide actions when not hovering
    });

    userActions.style.display = "none"; // Initially hide the actions
    chatWindow.appendChild(userMessage);
    if (DEBUG_MODE) console.debug("User message appended to chat window:", inputValue);

    // Add a progress bar to indicate processing
    const progressBarContainer = document.createElement("div");
    progressBarContainer.classList.add("progress-bar-container");
    const progressBar = document.createElement("div");
    progressBar.classList.add("progress-bar");
    progressBarContainer.appendChild(progressBar);
    chatWindow.appendChild(progressBarContainer);

    // Scroll to the bottom of the chat window
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        // Make a POST request to the server
        if (DEBUG_MODE) console.debug("Sending POST request to /handle-prompt/ endpoint.");
        const response = await fetch("/handle-prompt/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `user_prompt=${encodeURIComponent(inputValue)}`,
        });

        if (response.ok) {
            const jsonResponse = await response.json();
            if (DEBUG_MODE) console.debug("Response from server:", jsonResponse);

            if (jsonResponse.html_response) {
                const htmlContainer = document.createElement("div");
                htmlContainer.classList.add("response-container");
                htmlContainer.innerHTML = jsonResponse.html_response;
                chatWindow.appendChild(htmlContainer);

                // Add functionality for dynamically generated copy buttons
                const copyButtons = htmlContainer.querySelectorAll(".copy-button");
                copyButtons.forEach((button) => {
                    button.addEventListener("click", () => {
                        const codeBlock = button.nextElementSibling; // Assuming button is before <pre><code>
                        if (codeBlock) {
                            navigator.clipboard.writeText(codeBlock.innerText)
                                .then(() => {
                                    button.innerText = "Copied!";
                                    setTimeout(() => (button.innerText = "Copy"), 2000);
                                })
                                .catch((err) => console.error("Failed to copy:", err));
                        }
                    });
                });
            } else {
                const errorMessage = document.createElement("div");
                errorMessage.classList.add("message", "bot");
                errorMessage.innerText = "Error: No HTML content found in the response.";
                chatWindow.appendChild(errorMessage);
            }
        } else {
            throw new Error(`Server returned status ${response.status}`);
        }
    } catch (error) {
        console.error("Error during fetch:", error);

        const errorMessage = document.createElement("div");
        errorMessage.classList.add("message", "bot");
        errorMessage.innerText = "Error: Unable to process your request.";
        chatWindow.appendChild(errorMessage);
    } finally {
        progressBarContainer.remove();
        resetInputHeight();
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});

// ========================
// DYNAMIC INPUT RESIZING
// ========================
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

// ========================
// HANDLE ENTER AND SHIFT+ENTER
// ========================
userInput.addEventListener("keydown", (event) => {
    if (DEBUG_MODE) console.debug(`Keydown event detected: ${event.key}`);
    if (event.key === "Enter") {
        if (event.shiftKey) {
            if (DEBUG_MODE) console.debug("Shift+Enter detected. Allowing multiline input.");
            return;
        } else {
            event.preventDefault();
            document.getElementById("chat-form").dispatchEvent(new Event("submit"));
        }
    }
});

// ========================
// GLOBAL ERROR LOGGING
// ========================
window.addEventListener("error", (event) => {
    if (DEBUG_MODE) console.error("Uncaught error:", event.message);
});