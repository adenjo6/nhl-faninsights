// /pages/index.tsx
import { useEffect, useState } from "react";
import { searchRedditPosts, fetchRedditComments, buildGameQuery, RedditPost, RedditComment } from "../lib/reddit";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [posts, setPosts] = useState<RedditPost[]>([]);
  const [comments, setComments] = useState<Record<string, RedditComment[]>>({});
  const [error, setError] = useState<string | null>(null);

  // Example test query — swap with real teams/date as needed
  const query = buildGameQuery({ homeTeam: "Maple Leafs", awayTeam: "Canadiens", dateISO: "2025-04-02" });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const found = await searchRedditPosts({ query, limit: 3, sort: "new", time: "month" });
        if (cancelled) return;
        setPosts(found);

        // Optionally prefetch comments for the first post
        if (found[0]) {
          const c = await fetchRedditComments({ permalink: found[0].permalink, limit: 5, sort: "top" });
          if (!cancelled) setComments((prev) => ({ ...prev, [found[0].id]: c }));
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message ?? "Failed to fetch Reddit");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [query]);

  return (
    <main style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>NHL Fan Insights — Reddit Test</h1>
      <p>Query: <code>{query}</code></p>

      {loading && <p>Loading…</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {posts.map((p) => (
        <div key={p.id} style={{ border: "1px solid #e5e7eb", borderRadius: 12, padding: 16, marginTop: 12 }}>
          <a href={`https://www.reddit.com${p.permalink}`} target="_blank" rel="noreferrer">
            <h3 style={{ margin: 0 }}>{p.title}</h3>
          </a>
          <p style={{ margin: "6px 0 0 0", fontSize: 14, color: "#555" }}>
            r/{p.subreddit} • by {p.author} • ▲ {p.score} • 💬 {p.num_comments}
          </p>

          <button
            style={{ marginTop: 10 }}
            onClick={async () => {
              const cs = await fetchRedditComments({ permalink: p.permalink, limit: 5, sort: "top" });
              setComments((prev) => ({ ...prev, [p.id]: cs }));
            }}
          >
            Load Top Comments
          </button>

          {comments[p.id]?.length ? (
            <ul style={{ marginTop: 10 }}>
              {comments[p.id].map((c) => (
                <li key={c.id} style={{ marginBottom: 8 }}>
                  <strong>{c.author}</strong> • ▲ {c.score}
                  <div style={{ whiteSpace: "pre-wrap" }}>{c.body}</div>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ))}
    </main>
  );
}