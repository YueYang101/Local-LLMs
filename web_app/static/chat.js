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
}

// ========================
// FORM SUBMISSION EVENT HANDLER
// ========================
document.getElementById("chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const userInput = document.getElementById("user-input");
    const chatWindow = document.getElementById("chat-window");

    // Store the input value in a temporary variable
    const inputValue = userInput.value.trim(); // Trim whitespace

    if (!inputValue) {
        // If input is empty, do nothing
        return;
    }

    // Clear the input field after capturing the value
    userInput.value = "";

    // Add the user's message to the chat window
    const userMessage = document.createElement("div");
    userMessage.classList.add("message", "user");
    userMessage.innerText = inputValue;
    chatWindow.appendChild(userMessage);

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
        // Make a POST request to the /handle-prompt/ endpoint
        const response = await fetch("/handle-prompt/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `user_prompt=${encodeURIComponent(inputValue)}`,
        });

        if (response.ok) {
            const jsonResponse = await response.json(); // Parse JSON response
            if (DEBUG_MODE) console.debug("Response from server:", jsonResponse);

            if (jsonResponse.plain_text) {
                // Extract and display the plain text from the backend response
                const resultContainer = document.createElement("pre"); // Use <pre> to preserve formatting
                resultContainer.classList.add("response-container");
                resultContainer.textContent = jsonResponse.plain_text; // Extract and display plain text
                chatWindow.appendChild(resultContainer);
            } else if (jsonResponse.result) {
                // Fallback to display a general result if plain_text is not available
                const resultContainer = document.createElement("div");
                resultContainer.classList.add("response-container");
                resultContainer.textContent = jsonResponse.result; // Use textContent to display plain text
                chatWindow.appendChild(resultContainer);
            } else if (jsonResponse.error) {
                // Handle errors returned by the backend
                const errorMessage = document.createElement("div");
                errorMessage.classList.add("message", "bot");
                errorMessage.innerText = "Error: " + jsonResponse.error;
                chatWindow.appendChild(errorMessage);
            }
        } else {
            // Handle HTTP errors
            throw new Error(`Server returned status ${response.status}`);
        }
    } catch (error) {
        console.error("Error during fetch:", error);

        const errorMessage = document.createElement("div");
        errorMessage.classList.add("message", "bot");
        errorMessage.innerText = "Error: Unable to process your request.";
        chatWindow.appendChild(errorMessage);
    } finally {
        // Remove the progress bar
        progressBarContainer.remove();

        // Reset the input field's height after submission
        resetInputHeight();

        // Scroll to the bottom of the chat window
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});

// ========================
// DYNAMIC INPUT RESIZING
// ========================
const userInput = document.getElementById("user-input");

// Calculate line height from CSS and set defaults
const lineHeight = parseFloat(window.getComputedStyle(userInput).lineHeight); // Get line height from CSS
const maxHeight = 200; // Maximum height limit

// Save the initial height of the input field
const initialHeight = userInput.scrollHeight; // Save the initial scrollHeight

// Set the initial height explicitly based on scrollHeight
userInput.style.height = `${initialHeight}px`;

// Add event listener for dynamic resizing
userInput.addEventListener("input", () => {
    // Temporarily reset height to auto to ensure scrollHeight reflects content height
    userInput.style.height = "auto";

    // Calculate new height based on scrollHeight and limit it to maxHeight
    const newHeight = Math.min(userInput.scrollHeight, maxHeight);

    // Update the height
    userInput.style.height = `${newHeight}px`;
});

// ========================
// HANDLE ENTER AND SHIFT+ENTER
// ========================
userInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        if (event.shiftKey) {
            // Allow multiline input with Shift+Enter
            return;
        } else {
            // Prevent default Enter behavior and trigger form submission
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