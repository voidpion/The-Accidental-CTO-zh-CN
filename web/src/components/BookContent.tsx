import Markdown from "markdown-to-jsx";
import type { ReactNode } from "react";
import "./markdown-styles.css"; // Import your custom CSS
import { uniqueHeadingId } from "@/lib/headingIds";

interface BookContentProps {
  content: string;
}

const headingText = (children: unknown): string => {
  if (typeof children === "string" || typeof children === "number") return String(children);
  if (Array.isArray(children)) return children.map(headingText).join("");
  if (children && typeof children === "object" && "props" in children) {
    return headingText((children as { props?: { children?: unknown } }).props?.children);
  }
  return "";
};

export const BookContent = ({ content }: BookContentProps) => {
  const seenIds = new Map<string, number>();
  const Heading = ({ level, children, ...props }: { level: 1 | 2 | 3; children?: ReactNode; [key: string]: unknown }) => {
    const Tag = `h${level}` as "h1" | "h2" | "h3";
    const id = uniqueHeadingId(headingText(children), seenIds);
    return <Tag id={id} {...props}>{children}</Tag>;
  };

  return (
    <div className="h-full">
      <article className="max-w-[80vw] mx-auto pl-4 md:px-8 py-8">
        <div className="markdown-content">
          <Markdown options={{ overrides: {
            h1: { component: (props: Record<string, unknown>) => <Heading level={1} {...props} /> },
            h2: { component: (props: Record<string, unknown>) => <Heading level={2} {...props} /> },
            h3: { component: (props: Record<string, unknown>) => <Heading level={3} {...props} /> },
          } }}>
            {content}
          </Markdown>
        </div>
      </article>
    </div>
  );
};
