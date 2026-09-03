export const headingSlug = (text: string) => {
  const normalized = text
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "");
  return normalized || "section";
};

export const uniqueHeadingId = (text: string, seen: Map<string, number>) => {
  const base = headingSlug(text);
  const count = (seen.get(base) ?? 0) + 1;
  seen.set(base, count);
  return count === 1 ? base : `${base}-${count}`;
};
