"use client";
// "New request" can be asked for from the shell (key n, palette) while another screen is showing. The demo
// routes by URL hash, so a "#new" suffix cannot carry it; this tiny signal works in both builds.
let pending = false;
const EVT = "app:new-request";
export function askForNewRequest(): void { pending = true; window.dispatchEvent(new Event(EVT)); }
export function takeNewRequest(): boolean { const p = pending; pending = false; return p; }
export function onNewRequest(cb: () => void): () => void { window.addEventListener(EVT, cb); return () => window.removeEventListener(EVT, cb); }
