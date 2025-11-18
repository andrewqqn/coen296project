"use client";

import React, { useState, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2, Send, Trash2, Paperclip, X } from "lucide-react";
import { getAuthToken } from "@/lib/firebase";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface OrchestratorResponse {
  success: boolean;
  response: string | null;
  tools_used: string[];
  query: string;
  error: string | null;
}

export function OrchestratorQuery() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Function to format markdown text
  const formatMarkdown = (text: string) => {
    const lines = text.split('\n');
    const elements: JSX.Element[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];
    let codeBlockLang = '';

    lines.forEach((line, lineIndex) => {
      // Handle code blocks
      if (line.startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeBlockLang = line.slice(3).trim();
          codeBlockContent = [];
        } else {
          inCodeBlock = false;
          elements.push(
            <pre key={`code-${lineIndex}`} className="bg-muted p-3 rounded my-2 overflow-x-auto">
              <code className="text-xs">{codeBlockContent.join('\n')}</code>
            </pre>
          );
          codeBlockContent = [];
          codeBlockLang = '';
        }
        return;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        return;
      }

      // Process inline markdown
      const processInlineMarkdown = (text: string): (string | JSX.Element)[] => {
        const parts: (string | JSX.Element)[] = [];
        let remaining = text;
        let key = 0;

        while (remaining.length > 0) {
          // Bold (**text**)
          const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
          if (boldMatch && boldMatch.index !== undefined) {
            if (boldMatch.index > 0) {
              parts.push(remaining.slice(0, boldMatch.index));
            }
            parts.push(<strong key={`bold-${lineIndex}-${key++}`}>{boldMatch[1]}</strong>);
            remaining = remaining.slice(boldMatch.index + boldMatch[0].length);
            continue;
          }

          // Italic (*text* or _text_)
          const italicMatch = remaining.match(/(\*|_)(.+?)\1/);
          if (italicMatch && italicMatch.index !== undefined) {
            if (italicMatch.index > 0) {
              parts.push(remaining.slice(0, italicMatch.index));
            }
            parts.push(<em key={`italic-${lineIndex}-${key++}`}>{italicMatch[2]}</em>);
            remaining = remaining.slice(italicMatch.index + italicMatch[0].length);
            continue;
          }

          // Inline code (`code`)
          const codeMatch = remaining.match(/`(.+?)`/);
          if (codeMatch && codeMatch.index !== undefined) {
            if (codeMatch.index > 0) {
              parts.push(remaining.slice(0, codeMatch.index));
            }
            parts.push(
              <code key={`code-${lineIndex}-${key++}`} className="bg-muted px-1.5 py-0.5 rounded text-xs">
                {codeMatch[1]}
              </code>
            );
            remaining = remaining.slice(codeMatch.index + codeMatch[0].length);
            continue;
          }

          // Links ([text](url))
          const linkMatch = remaining.match(/\[(.+?)\]\((.+?)\)/);
          if (linkMatch && linkMatch.index !== undefined) {
            if (linkMatch.index > 0) {
              parts.push(remaining.slice(0, linkMatch.index));
            }
            parts.push(
              <a
                key={`link-${lineIndex}-${key++}`}
                href={linkMatch[2]}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary underline hover:no-underline"
              >
                {linkMatch[1]}
              </a>
            );
            remaining = remaining.slice(linkMatch.index + linkMatch[0].length);
            continue;
          }

          // No more matches, add remaining text
          parts.push(remaining);
          break;
        }

        return parts;
      };

      // Handle different line types
      // Headers
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={`h3-${lineIndex}`} className="text-base font-bold mt-3 mb-1">
            {processInlineMarkdown(line.slice(4))}
          </h3>
        );
      } else if (line.startsWith('## ')) {
        elements.push(
          <h2 key={`h2-${lineIndex}`} className="text-lg font-bold mt-3 mb-1">
            {processInlineMarkdown(line.slice(3))}
          </h2>
        );
      } else if (line.startsWith('# ')) {
        elements.push(
          <h1 key={`h1-${lineIndex}`} className="text-xl font-bold mt-3 mb-1">
            {processInlineMarkdown(line.slice(2))}
          </h1>
        );
      }
      // Unordered list
      else if (line.match(/^[\s]*[-*]\s/)) {
        const indent = line.match(/^[\s]*/)?.[0].length || 0;
        const content = line.replace(/^[\s]*[-*]\s/, '');
        elements.push(
          <div key={`li-${lineIndex}`} className="flex gap-2 my-1" style={{ marginLeft: `${indent * 8}px` }}>
            <span>•</span>
            <span>{processInlineMarkdown(content)}</span>
          </div>
        );
      }
      // Numbered list
      else if (line.match(/^[\s]*\d+\.\s/)) {
        const indent = line.match(/^[\s]*/)?.[0].length || 0;
        const number = line.match(/\d+/)?.[0];
        const content = line.replace(/^[\s]*\d+\.\s/, '');
        elements.push(
          <div key={`num-${lineIndex}`} className="flex gap-2 my-1" style={{ marginLeft: `${indent * 8}px` }}>
            <span>{number}.</span>
            <span>{processInlineMarkdown(content)}</span>
          </div>
        );
      }
      // Blockquote
      else if (line.startsWith('> ')) {
        elements.push(
          <div key={`quote-${lineIndex}`} className="border-l-4 border-primary/50 pl-3 my-2 italic text-muted-foreground">
            {processInlineMarkdown(line.slice(2))}
          </div>
        );
      }
      // Horizontal rule
      else if (line.match(/^(-{3,}|\*{3,}|_{3,})$/)) {
        elements.push(<hr key={`hr-${lineIndex}`} className="my-3 border-border" />);
      }
      // Regular paragraph
      else if (line.trim()) {
        elements.push(
          <p key={`p-${lineIndex}`} className="my-1">
            {processInlineMarkdown(line)}
          </p>
        );
      }
      // Empty line
      else {
        elements.push(<br key={`br-${lineIndex}`} />);
      }
    });

    return <div>{elements}</div>;
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const pdfFiles = Array.from(files).filter(
      (file) => file.type === "application/pdf"
    );

    if (pdfFiles.length !== files.length) {
      setError("Only PDF files are allowed");
      setTimeout(() => setError(null), 3000);
    }

    setAttachedFiles((prev) => [...prev, ...pdfFiles]);
    
    // Reset the input so the same file can be selected again if needed
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    
    // Store the current query before clearing
    const currentQuery = query.trim();
    const currentFiles = [...attachedFiles];

    try {
      // Get backend URL from environment
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      
      // Get Firebase token (will throw if not authenticated)
      const token = await getAuthToken();

      // Use FormData if there are files, otherwise use JSON
      let response;
      if (currentFiles.length > 0) {
        const formData = new FormData();
        formData.append("query", currentQuery);
        
        // Add message history if it exists
        if (conversationHistory.length > 0) {
          formData.append("message_history", JSON.stringify(conversationHistory));
        }
        
        // Add all attached files
        currentFiles.forEach((file) => {
          formData.append("files", file);
        });

        response = await fetch(`${backendUrl}/orchestrator/`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            // Don't set Content-Type - browser will set it with boundary for multipart/form-data
          },
          body: formData,
        });
      } else {
        response = await fetch(`${backendUrl}/orchestrator/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({ 
            query: currentQuery,
            message_history: conversationHistory.length > 0 ? conversationHistory : undefined
          }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data: OrchestratorResponse = await response.json();
      
      // Add user message and assistant response to conversation history
      if (data.success && data.response) {
        setConversationHistory(prev => [
          ...prev,
          { role: "user", content: currentQuery },
          { role: "assistant", content: data.response as string }
        ]);
      }
      
      // Clear the input and files on success
      if (data.success) {
        setQuery("");
        setAttachedFiles([]);
      } else {
        setError(data.error || "Unknown error occurred");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      console.error("Orchestrator error:", err);
    } finally {
      setLoading(false);
    }
  };
  
  const clearConversation = () => {
    setConversationHistory([]);
    setAttachedFiles([]);
    setError(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading) {
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-4">
      {/* Conversation History */}
      {conversationHistory.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-muted-foreground">
              Conversation ({conversationHistory.length / 2} messages)
            </p>
            <Button
              onClick={clearConversation}
              variant="ghost"
              size="sm"
              className="h-8 gap-2"
            >
              <Trash2 className="h-3 w-3" />
              Clear
            </Button>
          </div>
          
          <div className="max-h-96 overflow-y-auto space-y-3 p-4 rounded-lg border bg-muted/30">
            {conversationHistory.map((message, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg ${
                  message.role === "user"
                    ? "bg-primary/10 border border-primary/20 ml-8"
                    : "bg-card border mr-8"
                }`}
              >
                <p className="text-xs font-semibold mb-1 text-muted-foreground">
                  {message.role === "user" ? "You" : "Assistant"}
                </p>
                <div className="text-sm">
                  {message.role === "assistant" 
                    ? formatMarkdown(message.content)
                    : message.content
                  }
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Attached Files Display */}
      {attachedFiles.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-muted-foreground">
            Attached PDFs ({attachedFiles.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {attachedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-3 py-2 bg-primary/10 border border-primary/20 rounded-lg text-sm"
              >
                <span className="truncate max-w-[200px]">{file.name}</span>
                <span className="text-xs text-muted-foreground">
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
                <Button
                  onClick={() => removeFile(index)}
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 p-0 hover:bg-destructive/20"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input Section */}
      <div className="flex gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />
        <Button
          onClick={() => fileInputRef.current?.click()}
          variant="outline"
          size="icon"
          disabled={loading}
          title="Attach PDF documents"
        >
          <Paperclip className="h-4 w-4" />
        </Button>
        <Input
          type="text"
          placeholder="Ask me anything... (e.g., 'List all employees' or 'Show me all expenses')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          className="flex-1"
        />
        <Button
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
          size="icon"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive text-destructive">
          <p className="font-semibold">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
