import { launch } from "./cdp.mjs";
const b = await launch(9388);
await b.size(1280, 900);
for (const route of ["#/quote", "#/price-books", "#/kits", "#/"]) {
  await b.go("http://127.0.0.1:3203/index.html" + route); await b.sleep(900);
  const t = (await b.text()).replace(/\n+/g, " | ");
  console.log(route, "->", t.slice(0, 220));
}
await b.size(390, 844);
await b.go("http://127.0.0.1:3203/index.html#/quote"); await b.sleep(900);
console.log(JSON.stringify(await b.overflow()).slice(0, 200));
console.log("logs", b.logs.slice(0, 5));
b.close();
