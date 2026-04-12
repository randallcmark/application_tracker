const captureButton = document.getElementById("capture-button");
const optionsButton = document.getElementById("options-button");
const statusElement = document.getElementById("status");

function setStatus(message, isError = false) {
  statusElement.textContent = message;
  statusElement.classList.toggle("error", isError);
}

async function getActiveTab() {
  const tabs = await browser.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

async function extractCurrentPage(tabId) {
  const results = await browser.scripting.executeScript({
    target: { tabId },
    files: ["capture-page.js"]
  });
  return results && results[0] ? results[0].result : null;
}

async function captureCurrentTab() {
  captureButton.disabled = true;
  setStatus("Capturing...");

  try {
    const stored = await browser.storage.local.get({ trackerUrl: "", captureToken: "" });
    const trackerUrl = stored.trackerUrl.trim().replace(/\/$/, "");
    const captureToken = stored.captureToken.trim();
    if (!trackerUrl || !captureToken) {
      throw new Error("Open Settings and save tracker URL plus capture token first.");
    }

    const tab = await getActiveTab();
    if (!tab || !tab.id) {
      throw new Error("No active tab available.");
    }

    const payload = await extractCurrentPage(tab.id);
    if (!payload) {
      throw new Error("Could not extract page data.");
    }

    const response = await fetch(`${trackerUrl}/api/capture/jobs`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${captureToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || "Capture failed.");
    }

    setStatus(`${data.created ? "Captured" : "Updated"}: ${data.title}`);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    captureButton.disabled = false;
  }
}

captureButton.addEventListener("click", captureCurrentTab);
optionsButton.addEventListener("click", () => browser.runtime.openOptionsPage());
