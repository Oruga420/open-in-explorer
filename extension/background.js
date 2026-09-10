// Open in Explorer - MV3 service worker.
// Pulls a Windows path out of the current tab's URL and asks the native host
// to open it in File Explorer (selecting the file when the path is a file).

const HOST = "com.oruga.open_folder";
const PATH_KEYS = ["path", "folder", "dir", "file", "p", "url", "q", "text"];

// C:\..., C:/..., or \\server\share\...
// The lookbehind keeps URL schemes ("https://") from looking like a drive.
const WIN_PATH_RE =
  /(?:(?<![A-Za-z])[A-Za-z]:[\\/]|\\\\[^\\/:*?"<>|\r\n]+[\\/])[^\r\n"'<>|*]*/;

function safeDecode(s) {
  try {
    return decodeURIComponent(s.replace(/\+/g, " "));
  } catch (e) {
    return s;
  }
}

function tidy(p) {
  let s = p.trim();
  s = s.replace(/^["'`<(]+/, "").replace(/["'`>)]+$/, "");
  s = s.replace(/[.,;:]+$/, "");
  return s.trim();
}

function fromFileUrl(url) {
  let rest = url.slice("file://".length);
  if (rest.startsWith("/") && /^\/[A-Za-z][:|]/.test(rest)) {
    rest = rest.slice(1); // file:///C:/x -> C:/x
  } else if (!rest.startsWith("/")) {
    rest = "\\\\" + rest; // file://server/share -> UNC path
  }
  return safeDecode(rest).replace(/\|/, ":").replace(/\//g, "\\");
}

function matchPath(text) {
  const m = WIN_PATH_RE.exec(text);
  return m ? tidy(m[0]) : null;
}

// Returns a Windows path found in the URL, or null.
function extractPath(rawUrl) {
  if (!rawUrl) return null;
  const url = rawUrl.trim();

  if (/^file:\/\//i.test(url)) return fromFileUrl(url);

  let parsed = null;
  try {
    parsed = new URL(url);
  } catch (e) {
    /* not a real URL, fall through to the raw scan */
  }

  if (parsed) {
    // 1. Named query/hash params, most explicit first.
    const bags = [parsed.searchParams];
    if (parsed.hash.includes("=")) {
      bags.push(new URLSearchParams(parsed.hash.replace(/^#/, "")));
    }
    for (const bag of bags) {
      for (const key of PATH_KEYS) {
        for (const value of bag.getAll(key)) {
          const hit = matchPath(safeDecode(value));
          if (hit) return hit;
        }
      }
    }
    // 2. Any other param value.
    for (const bag of bags) {
      for (const [, value] of bag) {
        const hit = matchPath(safeDecode(value));
        if (hit) return hit;
      }
    }
  }

  // 3. Anywhere in the URL text (covers omnibox searches and pasted paths).
  return matchPath(safeDecode(url));
}

function notify(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icons/icon128.png",
    title,
    message
  });
}

function flash(text, color) {
  chrome.action.setBadgeBackgroundColor({ color });
  chrome.action.setBadgeText({ text });
  setTimeout(() => chrome.action.setBadgeText({ text: "" }), 2500);
}

function fileUrlFor(path) {
  const unc = path.startsWith("\\\\");
  const body = path.replace(/\\/g, "/");
  return unc ? "file:" + body : "file:///" + body;
}

function run(tab) {
  const path = extractPath(tab && tab.url);
  if (!path) {
    flash("?", "#b45309");
    notify(
      "No path in this URL",
      "Paste a Windows path (C:\\... or a \\\\server\\share path) in the address bar, then click again."
    );
    return;
  }

  chrome.runtime.sendNativeMessage(HOST, { action: "open", path }, (reply) => {
    if (chrome.runtime.lastError) {
      // Host not installed: fall back to Chrome's own directory listing.
      flash("!", "#b91c1c");
      notify(
        "Native helper not installed",
        "Run host\\install.ps1 once to open real Explorer windows. Opening in a tab instead."
      );
      chrome.tabs.create({ url: fileUrlFor(path) });
      return;
    }
    if (reply && reply.ok) {
      flash("OK", "#15803d");
    } else {
      flash("X", "#b91c1c");
      notify("Could not open", (reply && reply.error) || "Unknown error: " + path);
    }
  });
}

chrome.action.onClicked.addListener(run);

chrome.commands.onCommand.addListener((command) => {
  if (command !== "open-in-explorer") return;
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) run(tabs[0]);
  });
});
