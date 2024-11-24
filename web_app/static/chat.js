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
                // Create bot response container
                const botResponseContainer = document.createElement("div");
                botResponseContainer.classList.add("message-container");

                // Add the bot's message inside a <pre> tag
                const botMessage = document.createElement("pre");
                botMessage.classList.add("message", "bot");
                botMessage.innerText = data.result; // Render response as plain text
                botResponseContainer.appendChild(botMessage);

                // Add a Copy button
                const copyButton = document.createElement("button");
                copyButton.classList.add("copy-button");
                copyButton.innerText = "Copy";
                copyButton.addEventListener("click", () => {
                    navigator.clipboard.writeText(data.result).then(() => {
                        copyButton.innerText = "Copied!";
                        copyButton.classList.add("copied");
                        setTimeout(() => {
                            copyButton.innerText = "Copy";
                            copyButton.classList.remove("copied");
                        }, 2000);
                    });
                });

                // Append copy button at the top-right of the bot message container
                botResponseContainer.style.position = "relative";
                copyButton.style.position = "absolute";
                copyButton.style.top = "10px";
                copyButton.style.right = "10px";

                botResponseContainer.appendChild(copyButton);

                // Append bot response container to the chat window
                chatWindow.appendChild(botResponseContainer);
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