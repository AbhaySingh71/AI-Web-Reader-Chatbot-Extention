chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "fetchPageText") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.scripting.executeScript(
                {
                    target: { tabId: tabs[0].id },
                    function: () => document.body.innerText
                },
                (results) => {
                    if (results && results[0] && results[0].result) {
                        sendResponse({ text: results[0].result });
                    } else {
                        sendResponse({ text: "No text found on this page." });
                    }
                }
            );
        });
        return true; // Required for async response
    }
});
