"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { getAuthToken } from "@/lib/firebase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Upload, CheckCircle2, AlertCircle } from "lucide-react";

const EXPENSE_CATEGORIES = ["Travel", "Meals", "Conference", "Other"] as const;

export function ExpenseForm() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    amount: "",
    business_justification: "",
    category: "Other" as typeof EXPENSE_CATEGORIES[number],
    date_of_expense: new Date().toISOString().split("T")[0],
  });
  const [receiptFile, setReceiptFile] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      if (!receiptFile) {
        throw new Error("Please attach a receipt PDF");
      }

      if (!user?.uid) {
        throw new Error("User not authenticated");
      }

      // Get auth token
      const token = await getAuthToken();
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

      // Prepare form data for multipart upload
      const formDataToSend = new FormData();
      
      // Create expense data object
      // Note: employee_id will be set by backend from auth token (security)
      const expenseData = {
        amount: parseFloat(formData.amount),
        business_justification: formData.business_justification,
        category: formData.category,
        date_of_expense: new Date(formData.date_of_expense).toISOString(),
      };

      // Add expense data as JSON string
      formDataToSend.append("expense_data", JSON.stringify(expenseData));
      
      // Add receipt file
      formDataToSend.append("receipt", receiptFile);

      // Submit to backend - backend will determine employee_id from auth token
      const response = await fetch(`${backendUrl}/expenses`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formDataToSend,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to submit expense: ${response.statusText}`);
      }

      // Success!
      setSuccess(true);
      
      // Reset form
      setFormData({
        amount: "",
        business_justification: "",
        category: "Other",
        date_of_expense: new Date().toISOString().split("T")[0],
      });
      setReceiptFile(null);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error("Error submitting expense:", err);
      setError(err instanceof Error ? err.message : "Failed to submit expense");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 w-full max-w-2xl">
      {/* Date */}
      <div className="space-y-2">
        <Label htmlFor="date">Date of Expense</Label>
        <Input
          id="date"
          type="date"
          value={formData.date_of_expense}
          onChange={(e) =>
            setFormData({ ...formData, date_of_expense: e.target.value })
          }
          required
        />
      </div>

      {/* Amount */}
      <div className="space-y-2">
        <Label htmlFor="amount">Amount ($)</Label>
        <Input
          id="amount"
          type="number"
          step="0.01"
          min="0"
          placeholder="0.00"
          value={formData.amount}
          onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
          required
        />
      </div>

      {/* Category */}
      <div className="space-y-2">
        <Label htmlFor="category">Category</Label>
        <Select
          value={formData.category}
          onValueChange={(value) =>
            setFormData({ ...formData, category: value as typeof EXPENSE_CATEGORIES[number] })
          }
        >
          <SelectTrigger id="category">
            <SelectValue placeholder="Select a category" />
          </SelectTrigger>
          <SelectContent>
            {EXPENSE_CATEGORIES.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Business Justification */}
      <div className="space-y-2">
        <Label htmlFor="justification">Business Justification</Label>
        <Textarea
          id="justification"
          placeholder="Explain the business purpose of this expense..."
          value={formData.business_justification}
          onChange={(e) =>
            setFormData({ ...formData, business_justification: e.target.value })
          }
          required
          rows={4}
        />
      </div>

      {/* Receipt Upload */}
      <div className="space-y-2">
        <Label htmlFor="receipt">Receipt (PDF)</Label>
        <div className="flex items-center gap-2">
          <Input
            id="receipt"
            type="file"
            accept=".pdf,application/pdf"
            onChange={(e) => setReceiptFile(e.target.files?.[0] || null)}
            required
            className="flex-1"
          />
          {receiptFile && (
            <span className="text-sm text-muted-foreground">
              {receiptFile.name}
            </span>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-green-500/10 text-green-600">
          <CheckCircle2 className="h-4 w-4" />
          <span className="text-sm">Expense submitted successfully!</span>
        </div>
      )}

      {/* Submit Button */}
      <Button type="submit" disabled={loading} className="w-full">
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Submitting...
          </>
        ) : (
          <>
            <Upload className="mr-2 h-4 w-4" />
            Submit Expense
          </>
        )}
      </Button>
    </form>
  );
}
