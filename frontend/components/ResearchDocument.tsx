"use client";

import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

interface ResearchDocumentProps {
  markdown: string;
}

function processCitations(text: string): (string | JSX.Element)[] {
  const parts: (string | JSX.Element)[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const num = match[1];
    parts.push(
      <a
        key={`${match.index}-${num}`}
        href={`#source-${num}`}
        className="citation-link"
      >
        [{num}]
      </a>
    );
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

function processSourceLine(
  text: string
): { num: string; url: string; rest: string } | null {
  const match = text.match(/^(\d+)\.\s+(https?:\/\/\S+)(.*)/);
  if (match) {
    return { num: match[1], url: match[2], rest: match[3] };
  }
  return null;
}

function processChildren(children: React.ReactNode): React.ReactNode {
  if (typeof children === "string") {
    const parts = processCitations(children);
    return parts.length === 1 && typeof parts[0] === "string"
      ? parts[0]
      : parts;
  }

  if (Array.isArray(children)) {
    return children.map((child, i) => {
      if (typeof child === "string") {
        const parts = processCitations(child);
        return parts.length === 1 && typeof parts[0] === "string" ? (
          parts[0]
        ) : (
          <span key={i}>{parts}</span>
        );
      }
      return child;
    });
  }

  return children;
}

function extractText(children: React.ReactNode): string {
  if (typeof children === "string") return children;
  if (typeof children === "number") return String(children);
  if (Array.isArray(children)) return children.map(extractText).join("");
  if (
    children &&
    typeof children === "object" &&
    "props" in children &&
    (children as { props?: { children?: React.ReactNode } }).props
  ) {
    return extractText(
      (children as { props: { children?: React.ReactNode } }).props.children
    );
  }
  return "";
}

export default function ResearchDocument({ markdown }: ResearchDocumentProps) {
  const components: Components = useMemo(
    () => ({
      p({ children, ...props }) {
        return <p {...props}>{processChildren(children)}</p>;
      },
      li({ children, ...props }) {
        const textContent = extractText(children);
        const sourceLine = processSourceLine(textContent);

        if (sourceLine) {
          return (
            <li
              id={`source-${sourceLine.num}`}
              className="source-item"
              {...props}
            >
              <span className="text-[var(--fg-faint)]">
                [{sourceLine.num}]
              </span>{" "}
              <a
                href={sourceLine.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {sourceLine.url}
              </a>
              {sourceLine.rest && (
                <span className="text-[var(--fg-muted)]">
                  {sourceLine.rest}
                </span>
              )}
            </li>
          );
        }

        return <li {...props}>{processChildren(children)}</li>;
      },
      strong({ children, ...props }) {
        return <strong {...props}>{processChildren(children)}</strong>;
      },
      em({ children, ...props }) {
        return <em {...props}>{processChildren(children)}</em>;
      },
      h2({ children, ...props }) {
        const text = extractText(children);
        const id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-");
        const isSourcesHeading =
          text.toLowerCase() === "sources" ||
          text.toLowerCase() === "references";
        return (
          <h2 id={isSourcesHeading ? "sources-section" : id} {...props}>
            {children}
          </h2>
        );
      },
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      a({ href, children, node, ...props }) {
        return (
          <a
            {...props}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
          >
            {children}
          </a>
        );
      },
    }),
    []
  );

  return (
    <div className="prose-editorial">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
