# Project status — Open in Explorer

**Last updated:** 2026-09-10 12:15
**Phase:** v1.0.0 built, tested and published; waiting on the one manual load in Chrome
**Health:** green — every automated check passes; only the "Load unpacked" click is left

## Where it stands

The extension and its native helper are complete and pushed to
https://github.com/Oruga420/open-in-explorer (public). Clicking the toolbar button (or
Alt+Shift+E) reads the current tab's URL, pulls a Windows path out of it, and hands that path
to a small Python native messaging host that runs `explorer.exe` — `/select` when the path is
a file, so the file shows up highlighted inside its folder.

The native host is already installed on this laptop: `host\install.ps1` ran, wrote the launcher
and the host manifest, and registered the host under Chrome, Edge and Brave. The extension id
is pinned by the manifest `key` (`dahclepccpmepheckhenjdkfclfhdjib`), so the allow-list in the
host manifest matches on any machine.

What has not happened yet: the extension itself is not loaded in Chuck's Chrome profile.
`chrome://extensions` → Developer mode → **Load unpacked** →
`C:\Users\user\Desktop\oruga projects\open-in-explorer\extension`, then restart Chrome.

## Done

- URL → path extraction covering `file://`, query/hash params, UNC shares and raw pasted paths
  (verified: `node tests/extract.test.mjs`, 11/11 passing, including the `https:` false-positive
  that the drive-letter regex used to swallow)
- Python native messaging host, stdlib only, `ping` + `open` actions
  (verified: framed protocol driven from Python — `ping` answered, a real file answered
  `{"ok": true, "mode": "select"}` and Explorer opened with it selected, a bogus path answered
  `{"ok": false, "error": "Path not found: ..."}`)
- Launcher + registration through `host\install.ps1`
  (verified: ran it; `host\open_folder_host.bat` answers the protocol when called by absolute
  path, and the three `HKCU\...\NativeMessagingHosts\com.oruga.open_folder` keys exist)
- Icons generated from the stdlib, no image library (verified: rendered and eyeballed)
- Public repo created and pushed (verified: `gh repo create --push`, `main` at ea5d70c)
- Out-of-band machine change (registry + generated files) recorded in `.claude\bitacora.jsonl`

## Next

- Load the `extension` folder unpacked in Chrome, restart Chrome, pin the button
- Smoke test in the real browser: open `file:///C:/Users/user/Desktop/`, press Alt+Shift+E,
  confirm an Explorer window appears; then try a `?path=` URL and a `\\server\share` one
- If the badge shows `!` (host not found), re-run `host\install.ps1` and fully restart Chrome

## Blocked

- Automated end-to-end test in a throwaway Chrome — Chrome 152 no longer honours
  `--load-extension` (tried plain, `--enable-unsafe-extension-debugging` and
  `--disable-features=DisableLoadExtensionCommandLineSwitch`; the extension never appears as a
  CDP target). Not worth more time: the browser half runs on the same V8 the tests use, and the
  manual load is a one-time click anyway.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-09-10 | Native messaging host instead of just opening `file:///` in a tab | A `file://` tab is Chrome's own directory listing, not Explorer; the goal was a real Explorer window with the file selected |
| 2026-09-10 | Pin the extension id with a manifest `key` | The host's `allowed_origins` has to name the id; without a fixed key every unpacked load gets a new random id and the installer would need re-running |
| 2026-09-10 | `explorer.exe /select,<file>` for file paths | Highlights the file inside its folder without launching it — keeps the host from ever executing what it is handed |
| 2026-09-10 | Python + `.bat` launcher rather than a compiled host | Python is already on this machine and the host stays readable in the public repo; cost is a brief console flash, avoided by pointing at `pythonw.exe` |
| 2026-09-10 | Public GitHub repo | Explicit operator instruction, overriding the usual private-personal-repo default |

## Breakpoint log

### 2026-09-10 12:15 — v1.0.0 shipped to a public repo
- What: extension + native host + installer + tests + README written, host installed locally, repo created and pushed
- Files: `extension/` (manifest, background.js, icons), `host/` (open_folder_host.py, install.ps1, uninstall.ps1), `tests/extract.test.mjs`, `tools/make_icons.py`, README.md, LICENSE, .gitignore
- Verified: `node tests/extract.test.mjs` 11/11; native host protocol exercised directly and through the generated `.bat`; `gh repo create` pushed `main` (af8bab9, ea5d70c)
- Next: load unpacked in Chrome and smoke test the button
