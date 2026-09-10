// Checks the URL -> Windows path extraction used by the service worker.
//
//     node tests/extract.test.mjs
//
// The worker half of background.js is loaded on its own (everything up to the
// first chrome.* call) so the logic can run outside a browser.

import fs from "node:fs";

const source = fs.readFileSync(new URL("../extension/background.js", import.meta.url), "utf8");
const logic = source.split("function notify")[0] + "\nexport { extractPath };";
const { extractPath } = await import("data:text/javascript," + encodeURIComponent(logic));

const cases = [
  ["file:///C:/Users/me/Desktop/notes.md", "C:\\Users\\me\\Desktop\\notes.md"],
  ["file:///C:/Users/me/Desktop/oruga%20projects/", "C:\\Users\\me\\Desktop\\oruga projects\\"],
  ["file:///D:/", "D:\\"],
  ["file://nas01/media/movies", "\\\\nas01\\media\\movies"],
  ["https://www.google.com/search?q=C%3A%5CUsers%5Cme%5CDesktop%5Cnotes.txt", "C:\\Users\\me\\Desktop\\notes.txt"],
  ["https://example.com/x?path=C:/Temp/logs&z=1", "C:/Temp/logs"],
  ["https://example.com/#dir=%5C%5Cnas01%5Cmedia", "\\\\nas01\\media"],
  ['https://intranet/r?file=%22D%3A%5CShared%5CQ3%20report.xlsx%22', "D:\\Shared\\Q3 report.xlsx"],
  ["https://example.com/no/path/here", null],
  ["C:\\Users\\me\\Downloads", "C:\\Users\\me\\Downloads"],
  ["", null]
];

let failed = 0;
for (const [input, expected] of cases) {
  const actual = extractPath(input);
  const ok = actual === expected;
  if (!ok) failed++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${JSON.stringify(input)} -> ${JSON.stringify(actual)}` +
    (ok ? "" : `  (expected ${JSON.stringify(expected)})`));
}
console.log(`\n${cases.length - failed}/${cases.length} passed`);
process.exit(failed ? 1 : 0);
