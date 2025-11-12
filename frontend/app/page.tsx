"use client";

import { OrchestratorQuery } from "@/components/orchestrator-query";
import { Login, signOut } from "@/components/login";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Loader2, LogOut } from "lucide-react";

export default function Home() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <Login />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header with logout */}
      <header className="border-b">
        <div className="container mx-auto flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">ExpenSense</h2>
            <span className="text-sm text-muted-foreground">
              {user.email}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => signOut()}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Sign Out
          </Button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 items-center justify-center p-4">
        <main className="flex flex-col items-center gap-8 w-full max-w-4xl">
          <div className="flex flex-col items-center gap-4 text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground">
              ExpenSense
            </h1>
            <p className="text-lg text-muted-foreground">
              Ask questions in natural language about employees, expenses, policies, and audit logs
            </p>
          </div>
          
          <OrchestratorQuery />

          <div className="text-center text-sm text-muted-foreground space-y-2">
            <p className="font-semibold">Try these example queries:</p>
            <ul className="space-y-1">
              <li>&quot;List all employees&quot;</li>
              <li>&quot;Show me all expenses&quot;</li>
              <li>&quot;What are the reimbursement policies?&quot;</li>
              <li>&quot;Show me recent audit logs&quot;</li>
            </ul>
          </div>
        </main>
      </div>
    </div>
  );
}
