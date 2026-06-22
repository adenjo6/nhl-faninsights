import posthog from "posthog-js";

let initialized = false;

export function initPostHog(): void {
  if (typeof window === "undefined") return;
  if (initialized) return;

  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!key) return;

  posthog.init(key, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com",
    capture_pageview: false,
    person_profiles: "identified_only",
  });

  initialized = true;
}

export function capturePageview(url: string): void {
  if (!initialized) return;
  posthog.capture("$pageview", { $current_url: url });
}

export { posthog };
