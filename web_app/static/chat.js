const DEBUG_MODE = true;

// Attach event listener to the form
document.getElementById("chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const userInput = document.getElementById("user-input").value;
    const chatWindow = document.getElementById("chat-window");

    // Add the user's message to the chat window
    const userMessage = document.createElement("div");
    userMessage.classList.add("message", "user");
    userMessage.innerText = userInput;
    chatWindow.appendChild(userMessage);

    // Clear the input field
    document.getElementById("user-input").value = "";

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
        const response = await fetch("/list-folder/?folder_path=" + encodeURIComponent(userInput), {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (response.ok) {
            const jsonResponse = await response.json(); // Parse JSON response
            if (DEBUG_MODE) console.debug("Response from server:", jsonResponse);

            // Check if plain_text exists in the response
            if (jsonResponse.plain_text) {
                const plainText = jsonResponse.plain_text;

                // Display the plain text structure in the chat window
                const responseContainer = document.createElement("div");
                responseContainer.classList.add("response-container");
                responseContainer.textContent = plainText; // Display plain text directly
                chatWindow.appendChild(responseContainer);
            } else if (jsonResponse.error) {
                // Handle error response
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

        // Display generic error message in chat window
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

// Log uncaught errors in JavaScript for debugging
window.addEventListener("error", (event) => {
    if (DEBUG_MODE) console.error("Uncaught error:", event.message);
});