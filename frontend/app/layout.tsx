import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cortex — Deep Research Engine",
  description: "Multi-pass research with gap detection, source verification, and cumulative memory. Cheaper than Perplexity. Gets smarter with each use.",
  metadataBase: new URL("https://cortex.example.com"), // placeholder — update when deployed
  openGraph: {
    title: "Cortex — Deep Research Engine",
    description: "Search, verify, remember. Open-source deep research at ~10x lower cost.",
    type: "website",
    siteName: "Cortex",
  },
  twitter: {
    card: "summary_large_image",
    title: "Cortex — Deep Research Engine",
    description: "Search, verify, remember. Open-source deep research at ~10x lower cost.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            try {
              var stored = localStorage.getItem('cortex-theme');
              var dark = stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches);
              if (dark) document.documentElement.classList.add('dark');
            } catch(e) {}
          })();
        `}} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin=""
        />
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
