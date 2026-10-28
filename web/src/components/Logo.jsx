// Product mark: a Tenaga Red tile with a white bolt (the one sanctioned use of brand red as a fill).
// Purely presentational; the wordmark text stays in the markup next to it.
export default function Logo({ size = 24 }) {
  return (
    <svg className="logo-mark" width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      {/* exact Pantone 1795 C in both themes: a logo keeps its brand colour */}
      <rect width="64" height="64" rx="12" fill="#D22630" />
      <path d="M36 8 18 36h12l-4 20 20-30H34z" fill="#ffffff" />
    </svg>
  );
}
