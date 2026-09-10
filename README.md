# Open in Explorer

A Chrome extension for Windows: click the toolbar button and the folder whose path
is sitting in the address bar opens in a real File Explorer window — with the file
already selected if the path points at a file.

Chrome cannot open Explorer on its own, so the extension talks to a tiny Python
native messaging host that runs `explorer.exe` for it. That host is the only piece
that needs a one-time install.

## Install

1. **Register the native host** (needs Python 3 on `PATH`):

   ```powershell
   powershell -ExecutionPolicy Bypass -File host\install.ps1
   ```

   It writes `host\open_folder_host.bat`, `host\com.oruga.open_folder.json`, and the
   `HKCU\...\NativeMessagingHosts` key for Chrome, Edge and Brave.

2. **Load the extension**: `chrome://extensions` → enable **Developer mode** →
   **Load unpacked** → pick the `extension` folder.

3. **Restart Chrome** so it picks up the host registration, then pin the extension.

The extension id is pinned to `dahclepccpmepheckhenjdkfclfhdjib` by the `key` field
in the manifest, so it stays the same on every machine and matches what the installer
allow-lists. If you ever load a copy with the `key` removed, re-run the installer with
the id Chrome shows you:

```powershell
powershell -ExecutionPolicy Bypass -File host\install.ps1 -ExtensionId abcdefghijklmnop...
```

## Use

Put a path in the address bar and press the button (or **Alt+Shift+E**).

| What is in the URL | Example | What opens |
| --- | --- | --- |
| A `file://` URL | `file:///C:/Users/me/Desktop/notes.md` | Desktop, `notes.md` selected |
| A pasted path | `C:\Users\me\Downloads` | that folder |
| A path in a query param | `https://tracker/x?path=D:\Shared\Q3.xlsx` | `D:\Shared`, file selected |
| A path you searched for | `google.com/search?q=C:\Temp\logs` | `C:\Temp\logs` |
| A UNC share | `file://nas01/media/movies` | `\\nas01\media\movies` |

Params named `path`, `folder`, `dir`, `file`, `p`, `url`, `q` or `text` are checked
first, then any other param, then the URL text as a whole.

The badge flashes **OK** on success, **?** when there is no path in the URL, and **X**
when the path does not exist. If the native host is not installed, the extension falls
back to opening the path as a `file://` tab inside Chrome.

## Layout

```
extension/           the Chrome extension (MV3)
  manifest.json
  background.js      URL -> path extraction + native message
  icons/
host/
  open_folder_host.py   native messaging host (stdlib only)
  install.ps1           writes the launcher, manifest and registry keys
  uninstall.ps1         removes them
tests/extract.test.mjs  path extraction tests: node tests/extract.test.mjs
tools/make_icons.py     regenerates the icons
```

## Safety

The host accepts exactly two actions, `ping` and `open`. An `open` on a directory runs
`explorer.exe <dir>`; on a file it runs `explorer.exe /select,<file>`, which highlights
the file without launching it. Nothing else is executed, and Chrome only lets the
allow-listed extension id connect. Activity is logged to
`%LOCALAPPDATA%\open-in-explorer\host.log`.

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File host\uninstall.ps1
```

then remove the extension from `chrome://extensions`.

## Troubleshooting

- **"Native helper not installed" notification** — re-run `install.ps1` and restart
  Chrome completely (all windows).
- **Nothing happens** — open the service worker console from `chrome://extensions`
  and check `host.log` in `%LOCALAPPDATA%\open-in-explorer\`.
- **Moved the project folder** — the registry points at an absolute path; re-run
  `install.ps1` from the new location.

## License

MIT
