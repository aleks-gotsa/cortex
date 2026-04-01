const STORAGE_KEY = "cortex_api_keys";

export interface ApiKeys {
  anthropicApiKey: string;
  serperApiKey: string;
  tavilyApiKey: string;
}

export function getKeys(): ApiKeys | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ApiKeys;
  } catch {
    return null;
  }
}

export function saveKeys(keys: ApiKeys): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
}

export function clearKeys(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function hasKeys(): boolean {
  const k = getKeys();
  return !!(k?.anthropicApiKey && k?.serperApiKey && k?.tavilyApiKey);
}
