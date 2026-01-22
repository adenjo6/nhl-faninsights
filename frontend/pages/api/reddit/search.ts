// pages/api/reddit/search.ts
import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { q, subreddit = "hockey", limit = "5", sort = "new", t = "month" } = req.query;

  if (!q || typeof q !== "string") {
    res.status(400).json({ error: "Missing q param" });
    return;
  }

  const url = `https://www.reddit.com/r/${encodeURIComponent(String(subreddit))}/search.json` +
              `?q=${encodeURIComponent(q)}&restrict_sr=1&sort=${encodeURIComponent(String(sort))}` +
              `&t=${encodeURIComponent(String(t))}&limit=${encodeURIComponent(String(limit))}`;

  try {
    const r = await fetch(url, { headers: { "User-Agent": "nhl-fan-insights/1.0" } });
    if (!r.ok) {
      res.status(r.status).json({ error: `Upstream reddit error: ${r.status}` });
      return;
    }
    const data = await r.json();
    res.setHeader("Cache-Control", "s-maxage=300, stale-while-revalidate=300");
    res.status(200).json(data);
  } catch (e: any) {
    res.status(500).json({ error: e?.message ?? "proxy error" });
  }
}