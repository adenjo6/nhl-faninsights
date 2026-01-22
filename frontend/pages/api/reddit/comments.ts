// pages/api/reddit/comments.ts
import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { permalink, limit = "10", sort = "top" } = req.query;

  if (!permalink || typeof permalink !== "string") {
    res.status(400).json({ error: "Missing permalink param" });
    return;
  }

  const base = permalink.startsWith("/") ? `https://www.reddit.com${permalink}` : permalink;
  const url = `${base}.json?limit=${encodeURIComponent(String(limit))}&sort=${encodeURIComponent(String(sort))}`;

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