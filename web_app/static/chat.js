// Define DEBUG_MODE at the top of the file
const DEBUG_MODE = true;

// Attach event listener to the form
document.getElementById("chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const userInput = document.getElementById("user-input");
    const chatWindow = document.getElementById("chat-window");

    // Store the input value in a temporary variable
    const inputValue = userInput.value.trim(); // Trim whitespace

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

            if (jsonResponse.result) {
                // Display the result from the backend (LLM decision or output)
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

        // Scroll to the bottom of the chat window
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});

// Dynamic resizing logic for textarea
const userInput = document.getElementById("user-input");

// Ensure consistent default height before the user types
const lineHeight = parseFloat(window.getComputedStyle(userInput).lineHeight); // Get line height from CSS
const defaultHeight = lineHeight * 1; // Default height for 4 lines
const maxHeight = 200; // Maximum height limit
let previousHeight = defaultHeight; // Store the previous height to avoid redundant updates

userInput.style.height = `${defaultHeight}px`; // Explicitly set the default height

// Add event listener for dynamic resizing
userInput.addEventListener("input", () => {
    // Calculate the current scroll height of the content
    const scrollHeight = userInput.scrollHeight;

    // If the new height is different, adjust it
    if (scrollHeight !== previousHeight && scrollHeight > defaultHeight) {
        const newHeight = Math.min(scrollHeight, maxHeight);
        userInput.style.height = `${newHeight}px`;
        previousHeight = newHeight; // Update the previous height
    } else if (scrollHeight <= defaultHeight) {
        userInput.style.height = `${defaultHeight}px`; // Reset to default height if below threshold
        previousHeight = defaultHeight; // Update the previous height
    }
});

// Handle Enter and Shift+Enter behavior
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

// Log uncaught errors in JavaScript for debugging
window.addEventListener("error", (event) => {
    if (DEBUG_MODE) console.error("Uncaught error:", event.message);
});