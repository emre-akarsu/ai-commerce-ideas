import { launch } from "./cdp.mjs";
const b = await launch();
await b.size(390, 900, true);
for (const u of ["/", "/requests", "/requests/rq-1001", "/requests/rq-1002", "/requests/rq-1003", "/requests/rq-1004", "/requests/rq-1005", "/requests/rq-1006", "/requests/rq-1007", "/requests/rq-1008", "/vendors", "/setup", "/audit", "/approve/mock-approval-7"]) {
  await b.go("http://localhost:3100" + u);
  const o = await b.overflow();
  console.log(u.padEnd(28), "scrollW", o.scrollW, "of", o.w, o.bad.length ? JSON.stringify(o.bad) : "");
}
console.log("console:", b.logs.slice(0, 8));
b.close();
