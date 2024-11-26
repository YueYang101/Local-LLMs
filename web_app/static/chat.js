const DEBUG_MODE = true;

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

    if (DEBUG_MODE) console.debug("User input:", userInput);

    // Send the user's message to the server
    try {
        const response = await fetch("/handle-prompt/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `user_prompt=${encodeURIComponent(userInput)}`,
        });

        if (response.ok) {
            const data = await response.json();
            if (DEBUG_MODE) console.debug("Response from server:", data);

            if (data.result) {
                // Render HTML response content directly
                const responseContainer = document.createElement("div");
                responseContainer.classList.add("response-container");
                responseContainer.innerHTML = data.result; // Insert raw HTML
                chatWindow.appendChild(responseContainer);

                // Reattach event listeners for dynamically added links
                attachFileLinkListeners();
            } else if (data.error) {
                throw new Error(data.error);
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

// Function to attach event listeners to file links
function attachFileLinkListeners() {
    document.querySelectorAll(".file-link").forEach((link) => {
        link.addEventListener("click", async (event) => {
            event.preventDefault();
            const filePath = link.dataset.filePath;

            try {
                const response = await fetch(`/preview/?path=${encodeURIComponent(filePath)}`);
                if (response.ok) {
                    const content = await response.text();

                    // Display file content in modal
                    showModal(content);
                } else {
                    alert("Failed to load file content.");
                }
            } catch (error) {
                console.error("Error fetching file content:", error);
                alert("Error fetching file content.");
            }
        });
    });
}

// Function to display file content in a modal
function showModal(content) {
    const modal = document.createElement("div");
    modal.classList.add("modal");
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <pre>${content}</pre>
        </div>
    `;
    document.body.appendChild(modal);

    // Add event listener to close the modal
    modal.querySelector(".close-button").addEventListener("click", () => {
        modal.remove();
    });
}

// Close modal event listener for a fixed modal (if needed)
document.getElementById("close-modal")?.addEventListener("click", () => {
    const modal = document.getElementById("file-preview-modal");
    if (modal) {
        modal.style.display = "none";
    }
});

// Log uncaught errors in JavaScript for debugging
window.addEventListener("error", (event) => {
    if (DEBUG_MODE) console.error("Uncaught error:", event.message);
});