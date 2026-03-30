import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Cortex — Deep Research Engine";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OGImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#faf8f5",
          fontFamily: "serif",
        }}
      >
        <div
          style={{
            fontSize: 64,
            fontWeight: 700,
            color: "#1a1a1a",
            letterSpacing: "-2px",
            marginBottom: 12,
          }}
        >
          Cortex
        </div>
        <div
          style={{
            fontSize: 16,
            color: "#888",
            letterSpacing: "3px",
            textTransform: "uppercase",
            fontFamily: "monospace",
            marginBottom: 32,
          }}
        >
          SEARCH, VERIFY, REMEMBER.
        </div>
        <div
          style={{
            width: 200,
            height: 1,
            backgroundColor: "#e5e2dd",
            marginBottom: 32,
          }}
        />
        <div
          style={{
            fontSize: 14,
            color: "#bbb",
            fontFamily: "monospace",
          }}
        >
          open-source deep research engine
        </div>
      </div>
    ),
    { ...size }
  );
}
