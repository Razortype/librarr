const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class APIError extends Error {
  constructor(
    public status: number,
    public detail: string | Record<string, unknown>,
  ) {
    super(`API ${status}`);
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => res.statusText);
    throw new APIError(res.status, detail);
  }
  return res.json() as Promise<T>;
}
