import { useState, useEffect } from "react";
import { uniqueHeadingId } from "@/lib/headingIds";

interface Chapter {
  id: string;
  title: string;
  level: number;
}

export const useMarkdownContent = (url: string) => {
  const [content, setContent] = useState<string>("");
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContent = async () => {
      try {
        setLoading(true);
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error("Failed to fetch content");
        }
        const text = await response.text();
        setContent(text);

        // Parse chapters from markdown
        const chapterRegex = /^(#{1,3})\s+(.+)$/gm;
        const matches = [...text.matchAll(chapterRegex)];
        
        // Helper to strip markdown formatting from titles
        const stripMarkdown = (text: string) => {
          return text
            .replace(/\*\*/g, '') // Remove bold
            .replace(/\*/g, '')   // Remove italic
            .replace(/`/g, '')    // Remove code
            .replace(/^#+\s+/, '') // Remove heading markers
            .trim();
        };

        // Helper to create slug from heading text
        const seenIds = new Map<string, number>();
        const parsedChapters: Chapter[] = matches
          .map((match) => {
            const title = match[2].trim();
            return {
              id: uniqueHeadingId(stripMarkdown(title), seenIds),
              title: stripMarkdown(title),
              level: match[1].length,
            };
          })
          .filter((chapter) => chapter.title.length > 5 && !chapter.title.match(/^[A-Z\s]+$/));

        setChapters(parsedChapters);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [url]);

  return { content, chapters, loading, error };
};
