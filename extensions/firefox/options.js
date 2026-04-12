const trackerUrlInput = document.getElementById("tracker-url");
const captureTokenInput = document.getElementById("capture-token");
const statusElement = document.getElementById("status");
const form = document.getElementById("options-form");

async function loadOptions() {
  const stored = await browser.storage.local.get({
    trackerUrl: "http://127.0.0.1:8000",
    captureToken: ""
  });
  trackerUrlInput.value = stored.trackerUrl;
  captureTokenInput.value = stored.captureToken;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const trackerUrl = trackerUrlInput.value.trim().replace(/\/$/, "");
  const captureToken = captureTokenInput.value.trim();
  await browser.storage.local.set({ trackerUrl, captureToken });
  statusElement.textContent = "Settings saved.";
});

loadOptions();
