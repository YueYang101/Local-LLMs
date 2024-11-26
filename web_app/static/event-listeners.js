// Debug mode to log detailed messages (set to true for debugging)
const DEBUG_MODE = true;

// Attach a global event listener to dynamically handle clicks on file links
document.addEventListener("click", function (event) {
    // Check if the clicked element has the 'file-link' class
    if (event.target.classList.contains("file-link")) {
        event.preventDefault(); // Prevent default link behavior
        const filePath = event.target.dataset.filePath; // Extract the file path
        if (DEBUG_MODE) console.debug("File link clicked:", filePath);
        previewFile(filePath); // Trigger the preview function
    }
});

// Function to fetch and preview file content in a modal
async function previewFile(filePath) {
    try {
        if (DEBUG_MODE) console.debug("Fetching file content for:", filePath);
        
        // Send a request to fetch file content
        const response = await fetch(`/preview/?path=${encodeURIComponent(filePath)}`);
        
        if (response.ok) {
            const fileContent = await response.text(); // Get the file content
            if (DEBUG_MODE) console.debug("File content received:", fileContent);
            
            // Display the content in a modal
            showModal(fileContent);
        } else {
            console.error("Failed to fetch file content. Status:", response.status);
            alert("Failed to fetch file content. Please try again.");
        }
    } catch (error) {
        console.error("Error during file preview:", error);
        alert("An error occurred while fetching the file content.");
    }
}

// Function to dynamically create and display a modal with the file content
function showModal(content) {
    // Create the modal element
    const modal = document.createElement("div");
    modal.classList.add("popup-window");

    // Set modal content
    modal.innerHTML = `
        <button class="popup-close-button" title="Close">&times;</button>
        <div class="popup-content">
            <pre>${content}</pre>
        </div>
    `;

    // Add the modal to the body
    document.body.appendChild(modal);

    // Close the modal when the close button is clicked
    modal.querySelector(".popup-close-button").addEventListener("click", () => {
        modal.remove(); // Remove the modal from the DOM
        if (DEBUG_MODE) console.debug("Modal closed successfully.");
    });

    if (DEBUG_MODE) console.debug("Modal displayed successfully.");
}

// Global error logging for debugging unexpected JavaScript errors
window.addEventListener("error", (event) => {
    if (DEBUG_MODE) console.error("Uncaught error:", event.message, "at", event.filename, "line:", event.lineno);
});