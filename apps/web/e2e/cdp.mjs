import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";
const HS = process.env.CHROME_BIN || "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell";
export async function launch(port = 9333) {
  const proc = spawn(HS, ["--no-sandbox", "--disable-gpu", `--remote-debugging-port=${port}`, "--window-size=1280,900", "about:blank"], { stdio: "ignore" });
  let tab;
  for (let i = 0; i < 50; i++) {
    try { const r = await fetch(`http://127.0.0.1:${port}/json`); tab = (await r.json()).find((t) => t.type === "page"); if (tab) break; } catch {}
    await new Promise((r) => setTimeout(r, 200));
  }
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = new Map(); const logs = [];
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); }
    else if (d.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(d.params.type)) logs.push(d.params.type + ": " + d.params.args.map((a) => a.value ?? a.description).join(" "));
    else if (d.method === "Runtime.exceptionThrown") logs.push("exception: " + (d.params.exceptionDetails.exception?.description ?? d.params.exceptionDetails.text));
  };
  const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Page.enable"); await send("Runtime.enable");
  const api = {
    logs, send,
    async size(w, h, mobile = false) { await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile }); },
    async dark(on) { await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: on ? "dark" : "light" }] }); },
    async go(url) { await send("Page.navigate", { url }); await api.sleep(1500); },
    sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
    async ev(expr) { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result?.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description ?? "eval failed"); return r.result?.result?.value; },
    async text() { return api.ev("document.body.innerText"); },
    async click(label, scope = "") { // click the first visible button/link whose text includes label
      const ok = await api.ev(`(()=>{const root=document.querySelector(${JSON.stringify(scope || "body")})||document.body;const els=[...root.querySelectorAll('button,a,[role=option],summary,label')].filter(e=>e.offsetParent!==null&&!e.disabled&&(e.innerText||e.getAttribute('aria-label')||'').trim().includes(${JSON.stringify(label)}));if(!els.length)return false;els[0].click();return true})()`);
      await api.sleep(500); return ok;
    },
    async fill(sel, value) { await api.ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});const set=Object.getOwnPropertyDescriptor(e.constructor.prototype,'value').set;set.call(e,${JSON.stringify(value)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`); await api.sleep(150); },
    async key(key, mods = {}) { for (const type of ["keyDown", "keyUp"]) await send("Input.dispatchKeyEvent", { type, key, text: key.length === 1 ? key : undefined, windowsVirtualKeyCode: key.length === 1 ? key.toUpperCase().charCodeAt(0) : undefined, ...mods }); await api.sleep(300); },
    async shot(file) { const r = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false }); writeFileSync(file, Buffer.from(r.result.data, "base64")); },
    overflow: () => api.ev(`(()=>{const w=document.documentElement.clientWidth;const bad=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.right>w+1&&r.width>0&&!e.closest('[class*=overflow-x-auto]')}).slice(0,6).map(e=>e.tagName+'.'+(e.className||'').toString().slice(0,60)+' right='+Math.round(e.getBoundingClientRect().right));return {w,scrollW:document.documentElement.scrollWidth,bad}})()`),
    close() { try { ws.close(); } catch {} proc.kill(); },
  };
  return api;
}
