export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

export async function withMockFallback<T>(
  real: () => Promise<T>,
  mock: T,
): Promise<T> {
  if (USE_MOCK) return mock;
  return real();
}
