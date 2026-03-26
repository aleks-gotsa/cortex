"use client";

import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

interface DocumentViewProps {
  markdown: string;
}

/**
 * Replace citation patterns like [1], [2] with anchor links
 * that jump to the corresponding source in the Sources section.
 */
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
        className="text-blue-400 text-[0.8em] align-super font-semibold no-underline hover:text-blue-300 hover:underline"
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

/**
 * Check if a text node is inside a Sources list item like "1. http://..."
 * and convert numbered source URLs into anchor targets.
 */
function processSourceLine(
  text: string
): { num: string; url: string; rest: string } | null {
  const match = text.match(/^(\d+)\.\s+(https?:\/\/\S+)(.*)/);
  if (match) {
    return { num: match[1], url: match[2], rest: match[3] };
  }
  return null;
}

export default function DocumentView({ markdown }: DocumentViewProps) {
  const components: Components = useMemo(
    () => ({
      p({ children, ...props }) {
        const processed = processChildren(children);
        return <p {...props}>{processed}</p>;
      },
      li({ children, ...props }) {
        // Check if this is a source item (starts with a number and URL)
        const textContent = extractText(children);
        const sourceLine = processSourceLine(textContent);

        if (sourceLine) {
          return (
            <li id={`source-${sourceLine.num}`} {...props}>
              <span className="text-zinc-500 font-mono text-sm">
                [{sourceLine.num}]
              </span>{" "}
              <a
                href={sourceLine.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 underline underline-offset-2 break-all"
              >
                {sourceLine.url}
              </a>
              {sourceLine.rest && (
                <span className="text-zinc-400">{sourceLine.rest}</span>
              )}
            </li>
          );
        }

        const processed = processChildren(children);
        return <li {...props}>{processed}</li>;
      },
      strong({ children, ...props }) {
        const processed = processChildren(children);
        return <strong {...props}>{processed}</strong>;
      },
      em({ children, ...props }) {
        const processed = processChildren(children);
        return <em {...props}>{processed}</em>;
      },
      h2({ children, ...props }) {
        const text = extractText(children);
        const id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-");
        // If this is the Sources heading, add an id for jumping
        const isSourcesHeading =
          text.toLowerCase() === "sources" ||
          text.toLowerCase() === "references";
        return (
          <h2
            id={isSourcesHeading ? "sources-section" : id}
            {...props}
          >
            {children}
          </h2>
        );
      },
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      a({ href, children, node, target, rel, ...safeProps }) {
        return (
          <a
            {...safeProps}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 underline underline-offset-2"
          >
            {children}
          </a>
        );
      },
      pre({ children, ...props }) {
        return (
          <pre
            className="bg-[#171717] border border-zinc-800 rounded-lg p-4 overflow-x-auto my-4"
            {...props}
          >
            {children}
          </pre>
        );
      },
      code({ children, className, ...props }) {
        const isInline = !className;
        if (isInline) {
          return (
            <code
              className="bg-zinc-800 px-1.5 py-0.5 rounded text-[0.875em] font-[family-name:var(--font-geist-mono)]"
              {...props}
            >
              {children}
            </code>
          );
        }
        return (
          <code
            className={`${className ?? ""} font-[family-name:var(--font-geist-mono)] text-sm`}
            {...props}
          >
            {children}
          </code>
        );
      },
    }),
    []
  );

  return (
    <div className="prose w-full">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {markdown}
      </ReactMarkdown>
    </div>
  );
}

/** Recursively process children to replace citation patterns in text nodes. */
function processChildren(
  children: React.ReactNode
): React.ReactNode {
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

/** Extract raw text from React children for pattern matching. */
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
