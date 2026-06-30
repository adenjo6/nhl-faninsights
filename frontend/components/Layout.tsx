import Link from "next/link";
import { useRouter } from "next/router";

const NAV = [
  { href: "/", label: "Games" },
  { href: "/prospects", label: "Prospects" },
];

// Persistent top navigation, rendered on every page via _app. Gives the
// platform one front door and a single home for cross-feature links.
export default function Layout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isActive = (href: string) =>
    href === "/" ? router.pathname === "/" : router.pathname.startsWith(href);

  return (
    <div className="shell">
      <header className="nav">
        <div className="nav-inner">
          <Link href="/" className="brand">
            <span className="fin" aria-hidden="true">
              🦈
            </span>
            <span className="brand-text">
              Sharks<span className="brand-hub">Hub</span>
            </span>
          </Link>
          <nav className="links">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`link ${isActive(item.href) ? "on" : ""}`}
                aria-current={isActive(item.href) ? "page" : undefined}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <div className="content">{children}</div>

      <style jsx>{`
        .shell {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }
        .nav {
          position: sticky;
          top: 0;
          z-index: 50;
          background: var(--abyss);
          border-bottom: 2px solid var(--teal);
        }
        .nav-inner {
          max-width: 64rem;
          margin: 0 auto;
          padding: 0 1.25rem;
          height: 3.5rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .nav-inner :global(.brand) {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          text-decoration: none;
        }
        .fin {
          font-size: 1.1rem;
          line-height: 1;
        }
        .brand-text {
          font-family: var(--font-display);
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          font-size: 1.15rem;
          color: #fff;
        }
        .brand-hub {
          color: var(--orange);
          margin-left: 0.1em;
        }
        .links {
          display: flex;
          gap: 0.4rem;
        }
        /* :global() because Next's <Link> doesn't reliably forward styled-jsx's
           scope class to the underlying <a>; scoping under .links keeps it
           contained to the nav. */
        .links :global(.link) {
          font-family: var(--font-display);
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-size: 0.86rem;
          color: #cfe6e4;
          text-decoration: none;
          padding: 0.4rem 0.7rem;
          border-radius: 6px;
          transition: color 120ms, background 120ms;
        }
        .links :global(.link:hover) {
          color: #fff;
          background: rgba(255, 255, 255, 0.08);
        }
        .links :global(.link.on) {
          color: #fff;
        }
        .links :global(.link.on)::after {
          content: "";
          display: block;
          height: 2px;
          margin-top: 0.25rem;
          border-radius: 2px;
          background: var(--orange);
        }
        .links :global(.link:focus-visible) {
          outline: 2px solid var(--teal-bright);
          outline-offset: 2px;
        }
        .content {
          flex: 1;
        }
      `}</style>
    </div>
  );
}
