// Captures the screenshots in docs/mvp/screenshots from a running mock-mode web app (default http://localhost:3100).
import { launch } from "./cdp.mjs";
const base = process.env.WEB_URL || "http://localhost:3100";
const out = process.env.OUT_DIR || "../../../docs/mvp/screenshots";
const b = await launch();
const pages = [["inbox", "/"], ["request-questions", "/requests/rq-1001"], ["request-assumptions", "/requests/rq-1002"], ["suppliers-step", "/requests/rq-1003"],
  ["approve-and-send", "/requests/rq-1004"], ["waiting-for-replies", "/requests/rq-1005"], ["compare", "/requests/rq-1006"], ["waiting-for-approver", "/requests/rq-1007"],
  ["purchase-order", "/requests/rq-1008"], ["suppliers", "/vendors"], ["setup", "/setup"], ["audit", "/audit"], ["approval-link", "/approve/mock-approval-7"]];
for (const [mode, w, h, mobile, dark] of [["desktop", 1280, 900, false, false], ["mobile", 390, 844, false, false], ["dark", 1280, 900, false, true]]) {
  await b.dark(dark); await b.size(w, h, mobile);
  for (const [name, path] of pages) {
    if (mode !== "desktop" && !["inbox", "request-assumptions", "approve-and-send", "compare", "suppliers"].includes(name)) continue;
    await b.go(base + path); await b.sleep(900);
    await b.shot(`${out}/${mode}-${name}.png`);
  }
}
console.log("done", b.logs.length ? b.logs.slice(0, 3) : "no console errors");
b.close();
