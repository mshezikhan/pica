(function () {
  // ---- EXTENSION CONTEXT GUARD ----
  if (!chrome.runtime || !chrome.runtime.id) {
    return;
  }

  try {
    const CONTAINER_ID = "pica-overlay-container";
    const TRIGGER = "start_download";

    let overlayDismissed = false;
    let lastUrl = location.href;

    // ------------------------------
    // Add overlay button
    // ------------------------------
    function addOverlay() {
      if (overlayDismissed) return;
      if (document.getElementById(CONTAINER_ID)) return;

      // Normal video OR Shorts player
      const player =
        document.querySelector(".html5-video-player") ||
        document.querySelector("ytd-reel-video-renderer");

      if (!player) return;

      const style = getComputedStyle(player);
      if (!style || style.position === "static") {
        player.style.position = "relative";
      }

      const container = document.createElement("div");
      container.id = CONTAINER_ID;

      // ------------------------------
      // Download button
      // ------------------------------
      const downloadBtn = document.createElement("button");
      downloadBtn.className = "pica-download-btn";
      downloadBtn.title = "Download this video with Pica";

      const icon = document.createElement("img");
      icon.src = chrome.runtime.getURL("icons/download32.png");
      icon.alt = "Pica";

      const text = document.createElement("span");
      text.innerText = "Download with Pica";

      downloadBtn.appendChild(icon);
      downloadBtn.appendChild(text);

      downloadBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        e.preventDefault();

        try {
          // Copy raw URL, desktop app handles normalization
          navigator.clipboard.writeText(
            window.location.href + " " + TRIGGER
          );
        } catch (err) {
          // fail silently
        }

        overlayDismissed = true;
        container.remove();
      });

      // ------------------------------
      // Close button
      // ------------------------------
      const closeBtn = document.createElement("button");
      closeBtn.className = "pica-close-btn";
      closeBtn.innerText = "×";
      closeBtn.title = "Hide";

      closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        e.preventDefault();

        overlayDismissed = true;
        container.remove();
      });

      container.appendChild(downloadBtn);
      container.appendChild(closeBtn);
      player.appendChild(container);
    }

    // ------------------------------
    // Observe DOM (YouTube SPA)
    // ------------------------------
    const observer = new MutationObserver(() => {
      // Reset ONLY when URL changes
      if (location.href !== lastUrl) {
        lastUrl = location.href;
        overlayDismissed = false;

        const old = document.getElementById(CONTAINER_ID);
        if (old) old.remove();
      }

      addOverlay();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Initial run
    addOverlay();

  } catch (e) {
    // ---- SILENT FAIL ----
    if (
      e.message &&
      e.message.includes("Extension context invalidated")
    ) {
      return;
    }
  }
})();
