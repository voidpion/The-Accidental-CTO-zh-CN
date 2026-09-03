import { useState, useEffect } from "react";
import { BookSidebar } from "@/components/BookSidebar";
import { BookContent } from "@/components/BookContent";
import { useMarkdownContent } from "@/hooks/useMarkdownContent";
import { Loader2, ArrowUp } from "lucide-react";
import { Button } from "@/components/ui/button";

type Language = "zh" | "en";

const Index = () => {
  const [language, setLanguage] = useState<Language>("zh");
  const bookUrl = language === "zh" ? "/book-zh-cn.md" : "/test.md";
  const { content, chapters, loading, error } = useMarkdownContent(bookUrl);
  const [activeChapter, setActiveChapter] = useState("");
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    // Observe headings for active chapter tracking
    const headings = document.querySelectorAll(".markdown-content h1, .markdown-content h2, .markdown-content h3");
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const chapter = chapters.find((item) => item.id === entry.target.id);
            if (chapter) {
              setActiveChapter(chapter.id);
            }
          }
        });
      },
      { rootMargin: "-20% 0px -70% 0px" }
    );

    headings.forEach((heading) => observer.observe(heading));
    return () => observer.disconnect();
  }, [content, chapters]);

  useEffect(() => {
    setActiveChapter("");
  }, [language]);

  useEffect(() => {
    // Show scroll to top button when user scrolls down
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">The Accidental CTO</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center space-y-4 max-w-md">
          <h1 className="text-2xl font-bold text-destructive">Error Loading Book</h1>
          <p className="text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex max-h-screen overflow-y-scroll px-4  overflow-x-hidden max-w-[100vw]">
      <BookSidebar
        chapters={chapters}
        activeChapter={activeChapter}
        language={language}
        onLanguageChange={setLanguage}
      />
      <main className="top-20">
        <BookContent content={content} />
      </main>
      
      {showScrollTop && (
        <Button
          onClick={scrollToTop}
          size="icon"
          className="fixed bottom-8 right-8 rounded-full shadow-elegant z-50"
          aria-label="Scroll to top"
        >
          <ArrowUp className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
};

export default Index;
