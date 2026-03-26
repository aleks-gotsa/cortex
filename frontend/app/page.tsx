"use client";

import { ResearchInput } from "@/components/ResearchInput";

export default function Home() {
  return (
    <main className="mx-auto max-w-[800px] px-4 py-16">
      <h1 className="mb-2 text-3xl font-bold tracking-tight text-white">
        Cortex
      </h1>
      <p className="mb-10 text-sm text-gray-500">
        Deep research engine — search, verify, remember.
      </p>
      <ResearchInput />
    </main>
  );
}
