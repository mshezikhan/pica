(function () {
  // ---- EXTENSION CONTEXT GUARD ----
  if (!chrome.runtime || !chrome.runtime.id) {
    return;
  }

  try {
    const CONTAINER_ID = "pica-overlay-container";
    const TRIGGER = "start_download";

    let overlayDismissed = false;
    let lastVideoId = null;

    function getVideoId() {
      const url = new URL(window.location.href);
      return url.searchParams.get("v");
    }

    function getCleanVideoUrl() {
      const videoId = getVideoId();
      if (videoId) {
        return `https://www.youtube.com/watch?v=${videoId}`;
      }
      return window.location.href;
    }

    function addOverlay() {
      if (overlayDismissed) return;

      const player = document.querySelector(".html5-video-player");
      if (!player) return;
      if (document.getElementById(CONTAINER_ID)) return;

      if (getComputedStyle(player).position === "static") {
        player.style.position = "relative";
      }

      const container = document.createElement("div");
      container.id = CONTAINER_ID;

      // Download button
      const downloadBtn = document.createElement("button");
      downloadBtn.className = "pica-download-btn";
      downloadBtn.title = "Download this video with Pica.";

      const icon = document.createElement("img");

      // ---- SAFE ICON LOAD ----
      if (chrome.runtime && chrome.runtime.id) {
        icon.src = chrome.runtime.getURL("icons/download32.png");
      }

      icon.alt = "Pica";

      const text = document.createElement("span");
      text.innerText = "Download with Pica";

      downloadBtn.appendChild(icon);
      downloadBtn.appendChild(text);

      downloadBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        e.preventDefault();

        // ---- SAFE CLIPBOARD WRITE ----
        if (chrome.runtime && chrome.runtime.id) {
          navigator.clipboard.writeText(
            getCleanVideoUrl() + " " + TRIGGER
          );
        }

        overlayDismissed = true;
        container.remove();
      });

      // Close button
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

    function checkVideoChange() {
      const currentVideoId = getVideoId();

      if (currentVideoId && currentVideoId !== lastVideoId) {
        lastVideoId = currentVideoId;
        overlayDismissed = false;

        const old = document.getElementById(CONTAINER_ID);
        if (old) old.remove();
      }

      addOverlay();
    }

    // Observe DOM changes (YouTube SPA)
    const observer = new MutationObserver(checkVideoChange);
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Initial run
    checkVideoChange();

  } catch (e) {
    // ---- SILENTLY IGNORE EXTENSION INVALIDATION ----
    if (
      e.message &&
      e.message.includes("Extension context invalidated")
    ) {
      return;
    }
    console.error(e);
  }
})();
