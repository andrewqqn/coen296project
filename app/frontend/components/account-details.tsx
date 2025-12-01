"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, User, Mail, Building2, Shield, Wallet, DollarSign } from "lucide-react";

interface EmployeeDetails {
  employee_id: string;
  name: string;
  email: string;
  department: string;
  role: string;
}

interface BankAccountDetails {
  bank_account_id: string;
  holder_name: string;
  email: string;
  employee_id: string;
  balance: number;
}

export function AccountDetails() {
  const { user } = useAuth();
  const [employee, setEmployee] = useState<EmployeeDetails | null>(null);
  const [bankAccount, setBankAccount] = useState<BankAccountDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bankAccountError, setBankAccountError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!user) return;

      try {
        setLoading(true);
        setError(null);

        const token = await user.getIdToken();
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        
        // Fetch employee details
        const employeeResponse = await fetch(`${backendUrl}/employees/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!employeeResponse.ok) {
          throw new Error("Failed to fetch employee details");
        }

        const employeeData = await employeeResponse.json();
        setEmployee(employeeData);

        // Fetch bank account details
        try {
          const bankAccountResponse = await fetch(`${backendUrl}/bank-accounts/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (bankAccountResponse.ok) {
            const bankAccountData = await bankAccountResponse.json();
            setBankAccount(bankAccountData);
          } else {
            setBankAccountError("Bank account not found");
          }
        } catch (err) {
          setBankAccountError(err instanceof Error ? err.message : "Failed to fetch bank account");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!employee) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Account Found</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Unable to load your account details.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
          <CardDescription>Your employee account details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3">
            <User className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p className="text-base">{employee.name}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Mail className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Email</p>
              <p className="text-base">{employee.email}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Building2 className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Department</p>
              <p className="text-base">{employee.department}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Role</p>
              <p className="text-base capitalize">{employee.role}</p>
            </div>
          </div>

          <div className="flex items-start gap-3 pt-2 border-t">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Employee ID</p>
              <p className="text-sm font-mono text-muted-foreground">{employee.employee_id}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Bank Account</CardTitle>
          <CardDescription>Your linked bank account details</CardDescription>
        </CardHeader>
        <CardContent>
          {bankAccountError ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Wallet className="h-5 w-5" />
              <p className="text-sm">{bankAccountError}</p>
            </div>
          ) : bankAccount ? (
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <User className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Account Holder</p>
                  <p className="text-base">{bankAccount.holder_name}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <DollarSign className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Balance</p>
                  <p className="text-2xl font-semibold">${bankAccount.balance.toFixed(2)}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 pt-2 border-t">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Account ID</p>
                  <p className="text-sm font-mono text-muted-foreground">{bankAccount.bank_account_id}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center p-4">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
