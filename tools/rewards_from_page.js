/*
 * Read the reward names and backer counts off the Kickstarter rewards page.
 *
 * Kickstarter refuses GitHub Actions with a Cloudflare challenge, so the
 * numbers are carried across by hand: this runs in the browser, where the
 * page is already open and already passed the challenge.
 *
 * Use it on
 *   https://www.kickstarter.com/projects/tamj/we-are-all-one-heart-23-pieces-one-world/rewards
 *
 * Open the console (F12), paste the whole file, press Enter. The result is
 * printed and copied to the clipboard. Paste that into the "rewards_json"
 * box of the Update progress workflow.
 */
(() => {
  const out = {};

  // Strategy A: the reward list React renders from, if it is still in the page.
  const walk = (node) => {
    if (Array.isArray(node)) return node.forEach(walk);
    if (!node || typeof node !== "object") return;
    for (const [k, v] of Object.entries(node)) {
      if ((k === "rewards" || k === "items") && Array.isArray(v)) {
        for (const r of v) {
          const n = r && (r.backers_count ?? r.backersCount);
          if (r && r.title && Number.isInteger(n)) {
            out[r.title] = Math.max(n, out[r.title] ?? 0);
          }
        }
      }
      walk(v);
    }
  };
  for (const el of document.querySelectorAll("[data-initial],[data-project],[data-react-props],[data-rewards]")) {
    for (const a of el.attributes) {
      if (!a.name.startsWith("data-")) continue;
      try { walk(JSON.parse(a.value)); } catch (e) { /* not json */ }
    }
  }
  for (const s of document.querySelectorAll('script[type="application/json"]')) {
    try { walk(JSON.parse(s.textContent)); } catch (e) { /* not json */ }
  }

  // Strategy B: read what is on the screen. Every reward card shows a count
  // like "42 backers"; the title is the nearest heading above it.
  if (!Object.keys(out).length) {
    const isCount = /^\s*([\d,]+)\s*(backers?|支援者)\s*$/i;
    for (const el of document.querySelectorAll("div,span,p,li")) {
      if (el.children.length) continue;
      const m = isCount.exec(el.textContent || "");
      if (!m) continue;
      let box = el, title = "";
      for (let up = 0; up < 8 && box; up++, box = box.parentElement) {
        const h = box.querySelector("h1,h2,h3,h4,h5,[class*='title'],[class*='Title']");
        const t = h && h.textContent.trim();
        if (t && t.length > 2 && t.length < 140) { title = t; break; }
      }
      if (!title) continue;
      const n = parseInt(m[1].replace(/,/g, ""), 10);
      out[title] = Math.max(n, out[title] ?? 0);
    }
  }

  const names = Object.keys(out);
  const json = JSON.stringify(out);
  console.log(out);
  console.log("%c" + names.length + " rewards read", "font-weight:bold");
  if (names.length < 20) {
    console.warn("fewer than 20 rewards - scroll the whole page first, then run again");
  }
  try { copy(json); console.log("copied to the clipboard"); }
  catch (e) { console.log("copy this line:\n" + json); }
  return json;
})();
