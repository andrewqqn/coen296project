"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { getAuthToken } from "@/lib/firebase";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, AlertCircle, Receipt, Calendar, DollarSign, FileText } from "lucide-react";

interface Expense {
  expense_id: string;
  date_of_expense: string;
  employee_id: string;
  amount: number;
  business_justification: string;
  category: "Travel" | "Meals" | "Conference" | "Other";
  status: "pending" | "approved" | "rejected" | "admin_review";
  decision_actor?: string;
  decision_reason?: string;
  receipt_path?: string;
  submitted_at: string;
  updated_at: string;
}

interface Employee {
  employee_id: string;
  authentication_id: string;
  email: string;
  name: string;
  position: string;
  role: "employee" | "admin";
}

export function ExpenseList() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [employee, setEmployee] = useState<Employee | null>(null);

  useEffect(() => {
    if (user) {
      fetchData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = await getAuthToken();
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

      // Fetch current employee profile
      const employeeResponse = await fetch(`${backendUrl}/employees/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!employeeResponse.ok) {
        throw new Error("Failed to fetch employee profile");
      }

      const employeeData = await employeeResponse.json();
      setEmployee(employeeData);

      // Fetch expenses based on role
      let expensesData: Expense[];
      
      if (employeeData.role === "admin") {
        // Admin: fetch all expenses
        const expensesResponse = await fetch(`${backendUrl}/expenses`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!expensesResponse.ok) {
          throw new Error("Failed to fetch expenses");
        }

        expensesData = await expensesResponse.json();
      } else {
        // Employee: fetch only their expenses
        const expensesResponse = await fetch(`${backendUrl}/expenses`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!expensesResponse.ok) {
          throw new Error("Failed to fetch expenses");
        }

        const allExpenses = await expensesResponse.json();
        expensesData = allExpenses.filter(
          (exp: Expense) => exp.employee_id === user?.uid
        );
      }

      // Sort by submitted date (newest first)
      expensesData.sort((a, b) => 
        new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime()
      );

      setExpenses(expensesData);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError(err instanceof Error ? err.message : "Failed to load expenses");
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: Expense["status"]) => {
    switch (status) {
      case "approved":
        return <Badge variant="success">Approved</Badge>;
      case "rejected":
        return <Badge variant="destructive">Rejected</Badge>;
      case "admin_review":
        return <Badge variant="warning">Admin Review</Badge>;
      case "pending":
      default:
        return <Badge variant="secondary">Pending</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 rounded-md bg-destructive/10 text-destructive">
        <AlertCircle className="h-4 w-4" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">
            {employee?.role === "admin" ? "All Expenses" : "My Expenses"}
          </h2>
          <p className="text-sm text-muted-foreground">
            {expenses.length} {expenses.length === 1 ? "expense" : "expenses"} found
          </p>
        </div>
      </div>

      {expenses.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center p-12">
            <Receipt className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No expenses found</p>
            <p className="text-sm text-muted-foreground">
              Submit your first expense to get started
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {expenses.map((expense) => (
            <Card key={expense.expense_id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">
                      {expense.category} - {formatCurrency(expense.amount)}
                    </CardTitle>
                    <CardDescription>
                      Submitted on {formatDate(expense.submitted_at)}
                    </CardDescription>
                  </div>
                  {getStatusBadge(expense.status)}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Expense Date:</span>
                    <span className="font-medium">{formatDate(expense.date_of_expense)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Amount:</span>
                    <span className="font-medium">{formatCurrency(expense.amount)}</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-sm">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Business Justification:</span>
                  </div>
                  <p className="text-sm pl-6">{expense.business_justification}</p>
                </div>

                {expense.decision_reason && (
                  <div className="space-y-1 pt-2 border-t">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-muted-foreground">Decision Reason:</span>
                    </div>
                    <p className="text-sm pl-6">{expense.decision_reason}</p>
                  </div>
                )}

                {expense.receipt_path && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Receipt className="h-4 w-4" />
                    <span>Receipt attached</span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
