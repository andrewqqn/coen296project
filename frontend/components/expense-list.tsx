"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { getAuthToken } from "@/lib/firebase";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, AlertCircle, Receipt, Calendar, DollarSign, FileText, CheckCircle, XCircle, User, Mail } from "lucide-react";

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
  employee_name?: string;
  employee_email?: string;
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
  const [reviewingExpenseId, setReviewingExpenseId] = useState<string | null>(null);
  const [reviewReason, setReviewReason] = useState<string>("");
  const [submittingReview, setSubmittingReview] = useState(false);

  useEffect(() => {
    if (user) {
      fetchData();
    }
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

      // Fetch expenses - backend handles filtering based on role
      const expensesResponse = await fetch(`${backendUrl}/expenses`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!expensesResponse.ok) {
        throw new Error("Failed to fetch expenses");
      }

      const expensesData: Expense[] = await expensesResponse.json();

      // Sort by submitted date (newest first)
      expensesData.sort((a: Expense, b: Expense) => 
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

  const handleReview = async (expenseId: string, action: "approve" | "reject") => {
    if (!reviewReason.trim()) {
      setError("Please provide a reason for your decision");
      return;
    }

    setSubmittingReview(true);
    setError(null);

    try {
      const token = await getAuthToken();
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

      const formData = new FormData();
      formData.append("action", action);
      formData.append("reason", reviewReason);

      const response = await fetch(`${backendUrl}/expenses/${expenseId}/review`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to submit review");
      }

      // Refresh the expense list
      await fetchData();
      
      // Reset review state
      setReviewingExpenseId(null);
      setReviewReason("");
    } catch (err) {
      console.error("Error submitting review:", err);
      setError(err instanceof Error ? err.message : "Failed to submit review");
    } finally {
      setSubmittingReview(false);
    }
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
                {/* Employee Info - Admin Only */}
                {employee?.role === "admin" && (expense.employee_name || expense.employee_email) && (
                  <div className="pb-3 border-b">
                    <div className="grid grid-cols-1 gap-2 text-sm">
                      {expense.employee_name && (
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="text-muted-foreground">Employee:</span>
                          <span className="font-medium">{expense.employee_name}</span>
                        </div>
                      )}
                      {expense.employee_email && (
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <span className="text-muted-foreground">Email:</span>
                          <span className="font-medium">{expense.employee_email}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

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

                {/* Admin Review Section */}
                {employee?.role === "admin" && expense.status === "admin_review" && (
                  <div className="pt-4 border-t space-y-3">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                      <span>Admin Review Required</span>
                    </div>
                    
                    {reviewingExpenseId === expense.expense_id ? (
                      <div className="space-y-3">
                        <Textarea
                          placeholder="Enter reason for approval or rejection..."
                          value={reviewReason}
                          onChange={(e) => setReviewReason(e.target.value)}
                          className="min-h-[80px]"
                        />
                        <div className="flex gap-2">
                          <Button
                            onClick={() => handleReview(expense.expense_id, "approve")}
                            disabled={submittingReview || !reviewReason.trim()}
                            className="flex-1"
                            variant="default"
                          >
                            {submittingReview ? (
                              <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : (
                              <CheckCircle className="h-4 w-4 mr-2" />
                            )}
                            Approve
                          </Button>
                          <Button
                            onClick={() => handleReview(expense.expense_id, "reject")}
                            disabled={submittingReview || !reviewReason.trim()}
                            className="flex-1"
                            variant="destructive"
                          >
                            {submittingReview ? (
                              <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : (
                              <XCircle className="h-4 w-4 mr-2" />
                            )}
                            Reject
                          </Button>
                          <Button
                            onClick={() => {
                              setReviewingExpenseId(null);
                              setReviewReason("");
                            }}
                            disabled={submittingReview}
                            variant="outline"
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <Button
                        onClick={() => setReviewingExpenseId(expense.expense_id)}
                        variant="outline"
                        className="w-full"
                      >
                        Review Expense
                      </Button>
                    )}
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
