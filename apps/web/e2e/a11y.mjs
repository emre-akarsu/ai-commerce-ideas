// Runs axe-core on every screen of the demo build (served at DEMO_URL, default http://127.0.0.1:3300/page.html) in light and dark,
// at 1280 px and a true 390 px, and fails on any serious or critical violation. Disclosures are opened first so their content is checked.
// Usage: cd apps/web && npx vite build -c demo/vite.config.mjs && node demo/inline.mjs && python3 -m http.server 3300 --bind 127.0.0.1 --directory demo-dist &
//        node e2e/a11y.mjs
import { readFileSync } from "node:fs";
import { launch } from "./cdp.mjs";

const base = process.env.DEMO_URL || "http://127.0.0.1:3300/page.html";
const axe = readFileSync(new URL("../node_modules/axe-core/axe.min.js", import.meta.url), "utf8");
const routes = ["/", "/kits", "/price-books", "/quote", "/requests", "/requests/rq-1001", "/vendors", "/setup", "/audit", "/approve/mock-approval-7"];
const b = await launch(9477);
let bad = 0;
for (const [label, w, h, mobile, dark] of [["desktop light", 1280, 900, false, false], ["desktop dark", 1280, 900, false, true], ["mobile light", 390, 844, true, false], ["mobile dark", 390, 844, true, true]]) {
  await b.dark(dark); await b.size(w, h, mobile);
  for (const r of routes) {
    await b.go(`${base}#${r}`); await b.sleep(1200);
    await b.ev("document.querySelectorAll('details').forEach(d=>{d.open=true})"); await b.sleep(250);
    await b.ev(axe);
    const v = await b.ev(`axe.run(document,{resultTypes:['violations']}).then(r=>r.violations.filter(v=>v.impact==='serious'||v.impact==='critical').map(v=>({id:v.id,impact:v.impact,n:v.nodes.length,ex:v.nodes[0].target.join(' ').slice(0,80)})))`);
    if (v.length) { bad += v.length; console.log("FAIL", label, r, JSON.stringify(v)); } else console.log("ok  ", label, r);
  }
}
console.log(bad, "serious or critical violations");
b.close();
process.exit(bad ? 1 : 0);
