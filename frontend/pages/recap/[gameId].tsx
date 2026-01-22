// /pages/recap/[gameid].tsx
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  searchRedditPosts,
  fetchRedditComments,
  buildGameQuery,
  RedditPost,
  RedditComment,
} from "../../lib/reddit"; // NOTE: path from /pages/recap/[gameid].tsx → /lib/reddit.ts

import type { GetStaticProps, GetStaticPaths } from "next";

type Recap = {
  away_team: string;
  home_team: string;
  away_score: number;
  home_score: number;
  scorers: string[];
  // If your backend later returns a date, add it here (e.g., dateISO?: string)
};

export const getStaticPaths: GetStaticPaths = async () => ({
  paths: [],            // no pages pre-built at build time
  fallback: "blocking", // render on first request
});

export const getStaticProps: GetStaticProps<{ recap: Recap }> = async ({ params }) => {
  // IMPORTANT: folder name is [gameid], so the key is "gameid" (not "gameId")
  const id = params?.gameId;
  const res = await fetch(`http://localhost:8000/recap?game_id=${id}`);

  if (res.status === 404) {
    return { notFound: true };
  }
  if (!res.ok) {
    throw new Error(`Failed to fetch recap ${id}: ${res.status}`);
  }

  const recap: Recap = await res.json();

  return {
    props: { recap },
    revalidate: 86400, // revalidate once per day
  };
};

export default function RecapPage({ recap }: { recap: Recap }) {
  const router = useRouter();

  // Reddit state
  const [posts, setPosts] = useState<RedditPost[]>([]);
  const [comments, setComments] = useState<Record<string, RedditComment[]>>({});
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Build Reddit search query from recap data
  const redditQuery = useMemo(() => {
    if (!recap) return "";
    // If you have a game date from backend later, pass it as dateISO
    return buildGameQuery({
      homeTeam: recap.home_team,
      awayTeam: recap.away_team,
      // dateISO: recap.dateISO,
    });
  }, [recap]);

  // Fetch Reddit posts when query changes
  useEffect(() => {
    if (!redditQuery) return;
    let cancelled = false;

    (async () => {
      try {
        setLoadingPosts(true);
        setError(null);

        const found = await searchRedditPosts({
          query: redditQuery,
          limit: 5,
          sort: "new",
          time: "month",
        });

        if (!cancelled) setPosts(found);
      } catch (e: any) {
        if (!cancelled) setError(e?.message ?? "Failed to fetch Reddit posts");
      } finally {
        if (!cancelled) setLoadingPosts(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [redditQuery]);

  // Render
  // Note: with fallback:"blocking", router.isFallback is rarely seen on the client,
  // but harmless to keep for safety if you switch fallback modes later.
  if (router.isFallback) {
    return <div className="p-6 text-center">Loading recap…</div>;
  }

  const scorers = recap.scorers ?? [];

  return (
    <main className="max-w-6xl mx-auto p-6">
      <Link href="/" className="text-blue-600 hover:underline mb-4 block">
        ← Back to Archive
      </Link>

      <h1 className="text-3xl font-bold mb-4">
        {recap.away_team} @ {recap.home_team}
      </h1>
      <p className="text-xl mb-6">
        Final Score: {recap.away_score} – {recap.home_score}
      </p>

      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-2">Goal Scorers</h2>
        {scorers.length > 0 ? (
          <ul className="list-disc list-inside">
            {scorers.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        ) : (
          <p className="italic text-gray-500">No goals recorded.</p>
        )}
      </section>

      {/* Reddit Section */}
      <section className="mt-8">
        <h2 className="text-2xl font-semibold mb-3">Fan Buzz (Reddit)</h2>
        <p className="text-gray-600 mb-2">
          Searching for: <code>{redditQuery}</code>
        </p>

        {loadingPosts && <p>Loading Reddit posts…</p>}
        {error && <p className="text-red-600">{error}</p>}
        {!loadingPosts && !error && posts.length === 0 && (
          <p className="italic text-gray-500">No relevant threads found.</p>
        )}

        <div className="space-y-4">
          {posts.map((p) => (
            <div key={p.id} className="border rounded-lg p-4">
              <a
                href={`https://www.reddit.com${p.permalink}`}
                target="_blank"
                rel="noreferrer"
                className="hover:underline"
              >
                <h3 className="font-semibold">{p.title}</h3>
              </a>
              <p className="text-sm text-gray-500 mt-1">
                by {p.author} • ▲ {p.score} • 💬 {p.num_comments}
              </p>

              <button
                className="mt-3 text-sm px-3 py-1 rounded border hover:bg-gray-50"
                onClick={async () => {
                  const cs = await fetchRedditComments({
                    permalink: p.permalink,
                    limit: 8,
                    sort: "top",
                  });
                  setComments((prev) => ({ ...prev, [p.id]: cs }));
                }}
              >
                {comments[p.id]?.length ? "Refresh Top Comments" : "Load Top Comments"}
              </button>

              {comments[p.id]?.length ? (
                <ul className="mt-3 space-y-2">
                  {comments[p.id].map((c) => (
                    <li key={c.id} className="text-sm">
                      <strong>{c.author}</strong> • ▲ {c.score}
                      <div className="whitespace-pre-wrap">{c.body}</div>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
// import { GetStaticPaths, GetStaticProps } from "next";
// import Link from "next/link";
// import { useRouter } from "next/router";

// type Recap = {
//   away_team: string;
//   home_team: string;
//   away_score: number;
//   home_score: number;
//   scorers: string[];
// };

// export const getStaticPaths: GetStaticPaths = async () => ({
//   paths: [],            // no pages pre‐built at build time
//   fallback: "blocking", // build on first request
// });

// export const getStaticProps: GetStaticProps<{ recap: Recap }> = async ({ params }) => {
//   const id = params?.gameId;
//   const res = await fetch(`http://localhost:8000/recap?game_id=${id}`);
//   if (res.status === 404) {
//     return { notFound: true };
//   }
//   const recap: Recap = await res.json();

//   return {
//     props: { recap },
//     revalidate: 86400, // revalidate once per day
//   };
// };

// export default function RecapPage({ recap }: { recap: Recap }) {
//     const router = useRouter();
//     if (router.isFallback) {
//         return <div className="p-6 text-center">Loading recap…</div>;
//     }
//     const scorers = recap.scorers ?? [];

//     return (
//     <main className="max-w-6x1 mx-auto p-6">
//         <Link href="/" className="text-blue-600 hover:underline mb-4 block">
//         ← Back to Archive
//         </Link>
//         <h1 className="text-3xl font-bold mb-4">
//         {recap.away_team} @ {recap.home_team}
//         </h1>
//         <p className="text-xl mb-6">
//         Final Score: {recap.away_score} – {recap.home_score}
//         </p>

//         <section>
//         <h2 className="text-2xl font-semibold mb-2">Goal Scorers</h2>
//         {scorers.length > 0 ? (
//             <ul className="list-disc list-inside">
//             {scorers.map((s) => (
//                 <li key={s}>{s}</li>
//             ))}
//             </ul>
//         ) : (
//             <p className="italic text-gray-500">No goals recorded.</p>
//         )}
//         </section>
//     </main>
//     );
//     }