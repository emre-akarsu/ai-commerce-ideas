import fs from "node:fs";
const d = new URL("../demo-dist/", import.meta.url);
const js = fs.readFileSync(new URL("app.js", d), "utf8").replace(/<\/script/gi, "<\\/script");
const css = fs.readFileSync(new URL("app.css", d), "utf8");
const html = `<meta charset="utf-8">\n<title>Buy-side RFQ</title>\n<style>${css}</style>\n<div id="root"></div>\n<script type="module">${js}</script>\n`;
fs.writeFileSync(new URL("page.html", d), html);
console.log("page.html", html.length);
