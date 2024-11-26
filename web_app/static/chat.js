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
                // Create response container
                const responseContainer = document.createElement("div");
                responseContainer.classList.add("response-container");

                // Add response content
                const responseContent = document.createElement("pre");
                responseContent.classList.add("response-content");
                responseContent.innerText = data.result; // Render as plain text
                responseContainer.appendChild(responseContent);

                // Add a Copy button
                const copyButton = document.createElement("button");
                copyButton.classList.add("copy-button");
                copyButton.title = "Copy to clipboard";
                copyButton.innerHTML = `<i class="icon-copy"></i> Copy`;
                copyButton.addEventListener("click", () => {
                    navigator.clipboard.writeText(data.result).then(() => {
                        copyButton.classList.add("copied");
                        setTimeout(() => {
                            copyButton.classList.remove("copied");
                        }, 2000);
                    });
                });

                // Position the copy button on the upper-right corner
                copyButton.style.position = "absolute";
                copyButton.style.right = "10px";
                copyButton.style.top = "10px";
                responseContainer.appendChild(copyButton);

                // Append to chat window
                chatWindow.appendChild(responseContainer);
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