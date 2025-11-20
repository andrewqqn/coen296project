"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2, Send } from "lucide-react";
import { getAuthToken } from "@/lib/firebase";

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
  const [result, setResult] = useState<OrchestratorResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Get backend URL from environment
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      
      // Get Firebase token (will throw if not authenticated)
      const token = await getAuthToken();

      const response = await fetch(`${backendUrl}/orchestrator/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data: OrchestratorResponse = await response.json();
      setResult(data);
      
      // Clear the input on success
      if (data.success) {
        setQuery("");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      console.error("Orchestrator error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading) {
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-4">
      <div className="flex gap-2">
        <Input
          type="text"
          placeholder="Ask me anything... (e.g., 'List all employees' or 'Show me all expenses')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
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

      {result && (
        <div className="p-4 rounded-lg border bg-card space-y-3">
          {result.success ? (
            <>
              <div className="flex items-start justify-between">
                <p className="font-semibold text-foreground">Response</p>
                {result.tools_used.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {result.tools_used.map((tool) => (
                      <span
                        key={tool}
                        className="text-xs px-2 py-1 rounded-md bg-primary/10 text-primary"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {result.response}
              </p>
            </>
          ) : (
            <>
              <p className="font-semibold text-destructive">Failed</p>
              <p className="text-sm text-muted-foreground">
                {result.error || "Unknown error occurred"}
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
