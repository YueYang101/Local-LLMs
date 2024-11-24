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

    // Scroll to the bottom of the chat window
    chatWindow.scrollTop = chatWindow.scrollHeight;

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
            const botMessage = document.createElement("div");
            botMessage.classList.add("message", "bot");
            botMessage.innerHTML = data.result; // Render response as HTML
            chatWindow.appendChild(botMessage);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        } else {
            throw new Error("Error with the response");
        }
    } catch (error) {
        const errorMessage = document.createElement("div");
        errorMessage.classList.add("message", "bot");
        errorMessage.innerText = "Error: Unable to process your request.";
        chatWindow.appendChild(errorMessage);
    }
});