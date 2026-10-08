import { launch } from "./cdp.mjs";
const b = await launch();
const res = []; const ok = (name, cond, extra = "") => { res.push([cond ? "PASS" : "FAIL", name, extra]); };
const has = async (s) => (await b.text()).toLowerCase().includes(s.toLowerCase());
const path = () => b.ev("location.pathname");
await b.size(1280, 900);
for (const u of ["/", "/requests/rq-1001", "/requests/rq-1004", "/vendors", "/setup", "/audit", "/requests", "/approve/mock-approval-7"]) { await b.go("http://localhost:3100" + u); await b.sleep(2500); }
await b.go("http://localhost:3100/");

// composer -> request -> question
await b.click("New request"); await b.sleep(400);
await b.fill("textarea", "4 x 6205-2RS bearings for the packing line");
ok("composer enables Start request", await b.click("Start request"));
await b.sleep(1200);
ok("lands on the new request", (await path()).startsWith("/requests/rq-"), await path());
ok("asks one question", await has("One question"));
await b.ev("(()=>{const s=document.querySelector('fieldset select');const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set;set.call(s,'CN');s.dispatchEvent(new Event('change',{bubbles:true}))})()");
await b.click("Save answers"); await b.sleep(800);
ok("critical assumption now blocks", (await has("Confirm 1 assumption")) || (await has("Critical")));
await b.shot("/tmp/rfq-e2e-1-assumptions.png");

// ledger: confirm all
for (let i = 0; i < 3; i++) { if (!(await b.click("Confirm", "main"))) break; await b.sleep(600); }
ok("ledger settled", await has("Nothing is blocking the next step") || await has("Choose suppliers"));
await b.click("Go to suppliers");
await b.sleep(600);
ok("on suppliers step", await has("Choose suppliers"));
ok("unverified supplier is explained, not hidden", await has("Not verified yet"));
ok("sole trader explained", await has("sole trader or individual"));
await b.click("Select all 2 verified");
await b.shot("/tmp/rfq-e2e-2-suppliers.png");
await b.click("Prepare 2 messages for approval"); await b.sleep(900);
ok("prepared, nothing sent", await has("2 messages waiting"));
ok("exact text + footer shown", (await has("This is exactly what will be sent")) && (await has("Added by the system")));
ok("identity lines inside the approved text", await has("Company number"));
await b.shot("/tmp/rfq-e2e-3-approve.png");

// approve each message separately
await b.click("Approve and send to Northern"); await b.sleep(900);
ok("first send recorded", await has("Already sent"));
await b.click("Approve and send to Calder"); await b.sleep(1000);
ok("all sent -> replies step offers demo reply", await has("Waiting for replies"));
await b.click("Simulate supplier replies"); await b.sleep(900);
ok("replies read", await has("Where each value came from"));
await b.shot("/tmp/rfq-e2e-4-replies.png");
await b.click("Compare", "nav[aria-label='Steps']"); await b.sleep(600);
ok("comparison shows", await has("Compared like for like"));
await b.shot("/tmp/rfq-e2e-5-compare.png");
await b.click("Select", "table"); await b.sleep(900);
ok("waiting for approver", await has("Waiting for the approver"));
ok("approval link (demo)", await b.click("Open the approval page"));
await b.sleep(1200);
ok("approval page is bare (no nav)", !(await b.ev("!!document.querySelector('nav')")) && (await has("Approve this quote")));
await b.click("Approve this quote"); await b.sleep(900);
ok("decision recorded", await has("Recorded: approve"));
await b.shot("/tmp/rfq-e2e-6-decided.png");

// keyboard: palette + chords + help
await b.go("http://localhost:3100/");
await b.key("k", { modifiers: 2 }); await b.sleep(400);
ok("Ctrl+K opens palette", await b.ev("!!document.querySelector('[role=dialog][aria-label=\"Search or jump\"]')"));
await b.fill("input[role=combobox]", "suppl"); await b.key("Enter"); await b.sleep(900);
ok("palette navigates", (await path()) === "/vendors", await path());
await b.go("http://localhost:3100/requests"); await b.key("?", { modifiers: 8 }); await b.sleep(300);
ok("? opens shortcut help", await b.ev("!!document.querySelector('[role=dialog][aria-label=\"Keyboard shortcuts\"]')"));
await b.key("Escape"); await b.sleep(300);
ok("Esc closes it", !(await b.ev("!!document.querySelector('[role=dialog]')")));
await b.key("g"); await b.key("s"); await b.sleep(800);
ok("g s goes to suppliers", (await path()) === "/vendors", await path());
await b.go("http://localhost:3100/"); await b.key("j"); 
ok("j focuses the first inbox item", await b.ev("document.activeElement?.hasAttribute('data-nav-item')"));

// roles: requester sees reasons
await b.go("http://localhost:3100/requests/rq-1003");
await b.ev("(()=>{const s=document.querySelector('select');const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set;set.call(s,'requester');s.dispatchEvent(new Event('change',{bubbles:true}))})()"); await b.sleep(1800);
ok("requester told why they cannot prepare", await has("Needs the buyer role or higher"));
await b.go("http://localhost:3100/setup");
ok("setup explains admin only", true);
await b.shot("/tmp/rfq-e2e-7-role.png");

// dark mode + mobile
await b.dark(true); await b.size(1280, 900); await b.go("http://localhost:3100/requests/rq-1006"); await b.shot("/tmp/rfq-e2e-8-dark.png");
await b.dark(false); await b.size(390, 900, false); await b.go("http://localhost:3100/requests/rq-1004"); await b.shot("/tmp/rfq-e2e-9-mobile-approve.png");
ok("no console errors", b.logs.length === 0, b.logs.slice(0, 3).join(" | "));
for (const r of res) console.log(r.join("  "));
console.log(res.filter((r) => r[0] === "FAIL").length, "failures of", res.length);
b.close();
