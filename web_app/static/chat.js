// Attach event listener to the form
document.getElementById("chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const userInput = document.getElementById("user-input");
    const chatWindow = document.getElementById("chat-window");

    // Add the user's message to the chat window
    const userMessage = document.createElement("div");
    userMessage.classList.add("message", "user");
    userMessage.innerText = userInput.value;
    chatWindow.appendChild(userMessage);

    // Clear the input field
    userInput.value = "";

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
        const response = await fetch("/list-folder/?folder_path=" + encodeURIComponent(userInput.value), {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (response.ok) {
            const jsonResponse = await response.json(); // Parse JSON response
            if (DEBUG_MODE) console.debug("Response from server:", jsonResponse);

            // Check for plain_text in the response
            if (jsonResponse.plain_text) {
                const plainText = jsonResponse.plain_text;

                // Display the plain text structure
                const responseContainer = document.createElement("div");
                responseContainer.classList.add("response-container");
                responseContainer.textContent = plainText; // Use textContent to maintain plain text
                chatWindow.appendChild(responseContainer);
            } else if (jsonResponse.error) {
                const errorMessage = document.createElement("div");
                errorMessage.classList.add("message", "bot");
                errorMessage.innerText = "Error: " + jsonResponse.error;
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
        // Remove the progress bar
        progressBarContainer.remove();

        // Scroll to the bottom of the chat window
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});

// Add event listener to dynamically resize the textarea
const userInput = document.getElementById("user-input");
userInput.addEventListener("input", () => {
    // Reset the height to auto to calculate the new height correctly
    userInput.style.height = "auto";

    // Set the height based on the scroll height (content height)
    userInput.style.height = userInput.scrollHeight + "px";
});

// Log uncaught errors in JavaScript for debugging
window.addEventListener("error", (event) => {
    if (DEBUG_MODE) console.error("Uncaught error:", event.message);
});