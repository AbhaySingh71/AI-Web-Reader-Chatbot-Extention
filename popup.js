document.getElementById("askBtn").addEventListener("click", sendQuestion);
document.getElementById("userQuery").addEventListener("keypress", function (event) {
    if (event.key === "Enter") sendQuestion();
});

function sendQuestion() {
    let userQuery = document.getElementById("userQuery").value.trim();
    let chatMessages = document.getElementById("chatMessages");
    let loadingIndicator = document.getElementById("loadingIndicator");

    if (userQuery === "") return;

    // Add user message to chat
    let userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.innerText = userQuery;
    chatMessages.appendChild(userMessage);
    document.getElementById("userQuery").value = "";

    // Show loading indicator
    loadingIndicator.classList.remove("hidden");

    // Get the active tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        let pageUrl = tabs[0].url;

        fetch("http://127.0.0.1:5000/answer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: pageUrl, question: userQuery })
        })
        .then(response => response.json())
        .then(data => {
            console.log("API Response:", data); // Debugging log
            loadingIndicator.classList.add("hidden");

            // Handle undefined or empty answers
            const answerText = data?.answer ?? "⚠️ No answer received.";

            // Add AI response to chat
            let aiMessage = document.createElement("div");
            aiMessage.className = "ai-message";
            aiMessage.innerText = answerText;

            // Add copy button
            let copyBtn = document.createElement("span");
            copyBtn.className = "copy-btn";
            copyBtn.innerText = "📋";
            copyBtn.onclick = () => copyToClipboard(answerText);
            aiMessage.appendChild(copyBtn);

            chatMessages.appendChild(aiMessage);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            console.error("Error:", error);
            loadingIndicator.classList.add("hidden");

            let errorMessage = document.createElement("div");
            errorMessage.className = "error-message";
            errorMessage.innerText = "❌ Failed to fetch answer.";
            chatMessages.appendChild(errorMessage);
        });
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert("Copied to clipboard!");
    });
}
