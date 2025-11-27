"use client";

import { useState } from "react";
import { OrchestratorQuery } from "@/components/orchestrator-query";
import { ExpenseForm } from "@/components/expense-form";
import { ExpenseList } from "@/components/expense-list";
import { AccountDetails } from "@/components/account-details";
import { Login, signOut } from "@/components/login";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Loader2, LogOut, MessageSquare, Receipt, Upload, Menu, X, UserCircle } from "lucide-react";
import { cn } from "@/lib/utils";

type View = "query" | "expenses" | "submit" | "account";

export default function Home() {
  const { user, loading } = useAuth();
  const [activeView, setActiveView] = useState<View>("query");
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

  const navItems = [
    { id: "query" as View, label: "Query", icon: MessageSquare },
    { id: "expenses" as View, label: "Expenses", icon: Receipt },
    { id: "submit" as View, label: "Submit Expense", icon: Upload },
    { id: "account" as View, label: "Account", icon: UserCircle },
  ];

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r bg-background transition-transform duration-300 lg:relative lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header with frosted glass panel and glow effect */}
          <div className="relative border-b p-4">
            <div className="flex items-center justify-between">
              {/* Frosted glass panel with white glow behind it */}
              <div className="relative">
                {/* White glow burst behind the panel */}
                <div className="absolute inset-0 -z-10 overflow-hidden rounded-lg">
                  <div className="absolute left-1/2 top-1/2 h-28 w-48 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/20 blur-3xl" />
                  <div className="absolute left-1/2 top-1/2 h-20 w-36 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/30 blur-2xl" />
                </div>
                
                {/* Frosted glass panel */}
                <div className="rounded-lg backdrop-blur-md bg-background/50 border border-white/20 px-4 py-2 shadow-lg shadow-white/10">
                  <h2 className="text-xl font-semibold">ExpenSense</h2>
                </div>
              </div>
              
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveView(item.id);
                    setSidebarOpen(false);
                  }}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    activeView === item.id
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* User info and logout */}
          <div className="border-t p-4">
            <div className="mb-3 space-y-1">
              <p className="text-sm font-medium">{user.email}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => signOut()}
              className="w-full"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </Button>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Mobile header */}
        <header className="flex items-center gap-4 border-b p-4 lg:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <h2 className="text-lg font-semibold">ExpenSense</h2>
        </header>

        {/* Content area */}
        <main className="flex-1 overflow-auto">
          <div className="container mx-auto max-w-5xl p-6">
            {activeView === "query" && (
              <div className="space-y-8">
                <div className="space-y-2">
                  <h1 className="text-3xl font-bold tracking-tight">Query</h1>
                  <p className="text-muted-foreground">
                    Ask questions in natural language about employees, expenses, policies, and audit logs
                  </p>
                </div>
                
                <OrchestratorQuery />

                <div className="rounded-lg border bg-muted/50 p-4">
                  <p className="mb-2 text-sm font-semibold">Try these example queries:</p>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>&quot;List all employees&quot;</li>
                    <li>&quot;Show me all expenses&quot;</li>
                    <li>&quot;What are the reimbursement policies?&quot;</li>
                    <li>&quot;Show me recent audit logs&quot;</li>
                  </ul>
                </div>
              </div>
            )}

            {activeView === "expenses" && (
              <div className="space-y-6">
                <div className="space-y-2">
                  <h1 className="text-3xl font-bold tracking-tight">Expenses</h1>
                  <p className="text-muted-foreground">
                    View and manage your expense submissions
                  </p>
                </div>
                <ExpenseList />
              </div>
            )}

            {activeView === "submit" && (
              <div className="space-y-6">
                <div className="space-y-2">
                  <h1 className="text-3xl font-bold tracking-tight">Submit Expense</h1>
                  <p className="text-muted-foreground">
                    Submit a new expense report with receipt
                  </p>
                </div>
                <div className="flex justify-center">
                  <ExpenseForm />
                </div>
              </div>
            )}

            {activeView === "account" && (
              <div className="space-y-6">
                <div className="space-y-2">
                  <h1 className="text-3xl font-bold tracking-tight">Account</h1>
                  <p className="text-muted-foreground">
                    View your employee account details
                  </p>
                </div>
                <AccountDetails />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
