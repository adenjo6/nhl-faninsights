// /lib/reddit.ts
export type RedditPost = {
  id: string;
  title: string;
  permalink: string;
  url: string;
  score: number;
  num_comments: number;
  created_utc: number;
  author: string;
  subreddit: string;
};

export type RedditComment = {
  id: string;
  author: string;
  body: string;
  score: number;
  created_utc: number;
};

function encodeQ(q: string) {
  return encodeURIComponent(q.trim());
}

const isBrowser = typeof window !== "undefined";

/** Normalize posts from Reddit API shape */
function normalizePosts(data: any): RedditPost[] {
  return (
    data?.data?.children?.map((c: any) => {
      const p = c?.data ?? {};
      return {
        id: p.id,
        title: p.title,
        permalink: p.permalink,
        url: p.url,
        score: p.score,
        num_comments: p.num_comments,
        created_utc: p.created_utc,
        author: p.author,
        subreddit: p.subreddit,
      } as RedditPost;
    }) ?? []
  );
}

/** Normalize comments from Reddit API shape */
function normalizeComments(data: any): RedditComment[] {
  const commentsListing = data?.[1]?.data?.children ?? [];
  return commentsListing
    .filter((c: any) => c.kind === "t1")
    .map((c: any) => {
      const d = c.data;
      return {
        id: d.id,
        author: d.author,
        body: d.body,
        score: d.score,
        created_utc: d.created_utc,
      } as RedditComment;
    });
}

/**
 * Search posts (uses Next API in browser to avoid CORS; direct on server).
 */
export async function searchRedditPosts({
  query,
  subreddit = "hockey",
  limit = 5,
  sort = "new",
  time = "month",
}: {
  query: string;
  subreddit?: string;
  limit?: number;
  sort?: "relevance" | "new" | "top" | "comments";
  time?: "hour" | "day" | "week" | "month" | "year" | "all";
}): Promise<RedditPost[]> {
  let res: Response;

  if (isBrowser) {
    const url = `/api/reddit/search?q=${encodeQ(query)}&subreddit=${encodeQ(
      subreddit
    )}&limit=${limit}&sort=${encodeQ(sort)}&t=${encodeQ(time)}`;
    res = await fetch(url);
  } else {
    // server-side (e.g., getStaticProps) can hit Reddit directly
    const url = `https://www.reddit.com/r/${encodeQ(subreddit)}/search.json?q=${encodeQ(
      query
    )}&restrict_sr=1&sort=${encodeQ(sort)}&t=${encodeQ(String(time))}&limit=${limit}`;
    res = await fetch(url, { headers: { "User-Agent": "nhl-fan-insights/1.0" } });
  }

  if (!res.ok) throw new Error(`Reddit search failed: ${res.status} ${res.statusText}`);
  const data = await res.json();
  return normalizePosts(data);
}

/**
 * Fetch top-level comments for a given post permalink (same proxy logic).
 */
export async function fetchRedditComments({
  permalink,
  limit = 10,
  sort = "top",
}: {
  permalink: string;
  limit?: number;
  sort?: "confidence" | "top" | "new" | "controversial" | "old" | "random" | "qa";
}): Promise<RedditComment[]> {
  let res: Response;

  if (isBrowser) {
    const url = `/api/reddit/comments?permalink=${encodeQ(permalink)}&limit=${limit}&sort=${encodeQ(sort)}`;
    res = await fetch(url);
  } else {
    const base = permalink.startsWith("/") ? `https://www.reddit.com${permalink}` : permalink;
    const url = `${base}.json?limit=${limit}&sort=${encodeQ(sort)}`;
    res = await fetch(url, { headers: { "User-Agent": "nhl-fan-insights/1.0" } });
  }

  if (!res.ok) throw new Error(`Reddit comments failed: ${res.status} ${res.statusText}`);
  const data = await res.json();
  return normalizeComments(data);
}

/** Helper to form a reasonable query for a game */
export function buildGameQuery({ homeTeam, awayTeam, dateISO }: { homeTeam: string; awayTeam: string; dateISO?: string }) {
  const parts = [`${awayTeam} vs ${homeTeam}`];
  if (dateISO) parts.push(dateISO);
  return parts.join(" ");
}