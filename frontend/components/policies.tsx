"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, AlertCircle, FileText, DollarSign, Receipt } from "lucide-react";

export function Policies() {
  return (
    <div className="space-y-6">
      {/* Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Expense Reimbursement Policy Overview
          </CardTitle>
          <CardDescription>
            All expense submissions are subject to automated review based on the following policies and rules
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Approval Decision Rules */}
      <Card>
        <CardHeader>
          <CardTitle>Automated Approval Rules</CardTitle>
          <CardDescription>
            The system applies these rules in order to determine expense approval status
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Rule R1 */}
          <div className="flex gap-4 rounded-lg border p-4">
            <div className="flex-shrink-0">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
            </div>
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                  R1: Auto-Approve
                </Badge>
              </div>
              <p className="text-sm font-medium">Automatic Approval (≤ $500, First Request of Day)</p>
              <p className="text-sm text-muted-foreground">
                Expenses are automatically approved when ALL conditions are met:
              </p>
              <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
                <li>Amount ≤ $500</li>
                <li>First submission of the day for the employee</li>
                <li>Receipt is readable and valid</li>
                <li>OCR data matches submitted metadata</li>
                <li>Category is reimbursable</li>
                <li>No policy conflicts detected</li>
                <li>Expense appears reasonable for the category</li>
              </ul>
            </div>
          </div>

          {/* Rule R2 */}
          <div className="flex gap-4 rounded-lg border p-4">
            <div className="flex-shrink-0">
              <AlertCircle className="h-6 w-6 text-orange-600" />
            </div>
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
                  R2: Manual Review
                </Badge>
              </div>
              <p className="text-sm font-medium">Frequency Violation (≤ $500 but NOT first request today)</p>
              <p className="text-sm text-muted-foreground">
                If an employee has already submitted a request today, additional requests ≤ $500 require manual review to detect:
              </p>
              <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
                <li>Repeated amounts or merchants</li>
                <li>Back-to-back submissions</li>
                <li>Possible split receipts</li>
              </ul>
            </div>
          </div>

          {/* Rule R3 */}
          <div className="flex gap-4 rounded-lg border p-4">
            <div className="flex-shrink-0">
              <AlertCircle className="h-6 w-6 text-blue-600" />
            </div>
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                  R3: Manual Review
                </Badge>
              </div>
              <p className="text-sm font-medium">Large Amount (&gt; $500)</p>
              <p className="text-sm text-muted-foreground">
                Any expense over $500 always requires manual review by an administrator, regardless of other factors.
              </p>
            </div>
          </div>

          {/* Rule R4 */}
          <div className="flex gap-4 rounded-lg border p-4">
            <div className="flex-shrink-0">
              <XCircle className="h-6 w-6 text-red-600" />
            </div>
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                  R4: Auto-Reject
                </Badge>
              </div>
              <p className="text-sm font-medium">Invalid Documentation</p>
              <p className="text-sm text-muted-foreground">
                Expenses are automatically rejected when:
              </p>
              <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
                <li>Receipt is missing or unreadable</li>
                <li>Receipt is corrupted or cropped</li>
                <li>OCR data does not match submitted amount</li>
                <li>Essential fields are missing (vendor, date, amount, itemization)</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Receipt Requirements */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Receipt className="h-5 w-5" />
            Receipt Requirements
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            A valid receipt must clearly show:
          </p>
          <ul className="text-sm space-y-2 ml-4 list-disc">
            <li>Vendor/merchant name</li>
            <li>Date of transaction</li>
            <li>Itemized list of charges</li>
            <li>Total amount</li>
            <li>Taxes and fees (if applicable)</li>
            <li>Payment method</li>
          </ul>
          <p className="text-sm text-muted-foreground mt-4">
            Receipts must be readable and not cropped. Blurry or incomplete receipts will be rejected.
          </p>
        </CardContent>
      </Card>

      {/* Eligible Categories */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Eligible Categories & Limits
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b">
              <div>
                <p className="text-sm font-medium">Meals</p>
                <p className="text-xs text-muted-foreground">Business or travel meals</p>
              </div>
              <Badge variant="secondary">≤ $120/day</Badge>
            </div>
            
            <div className="flex justify-between items-center py-2 border-b">
              <div>
                <p className="text-sm font-medium">Supplies</p>
                <p className="text-xs text-muted-foreground">Office or business supplies</p>
              </div>
              <Badge variant="secondary">≤ $200/item</Badge>
            </div>
            
            <div className="flex justify-between items-center py-2 border-b">
              <div>
                <p className="text-sm font-medium">Hotels</p>
                <p className="text-xs text-muted-foreground">Lodging for business travel</p>
              </div>
              <Badge variant="secondary">≤ $500/day</Badge>
            </div>
            
            <div className="flex justify-between items-center py-2 border-b">
              <div>
                <p className="text-sm font-medium">Travel</p>
                <p className="text-xs text-muted-foreground">Airfare, transportation, parking, tolls</p>
              </div>
              <Badge variant="secondary">Varies</Badge>
            </div>
            
            <div className="flex justify-between items-center py-2 border-b">
              <div>
                <p className="text-sm font-medium">Conference</p>
                <p className="text-xs text-muted-foreground">Registration fees and related costs</p>
              </div>
              <Badge variant="secondary">No limit</Badge>
            </div>
            
            <div className="flex justify-between items-center py-2">
              <div>
                <p className="text-sm font-medium">Other</p>
                <p className="text-xs text-muted-foreground">Must be business-related</p>
              </div>
              <Badge variant="secondary">Case-by-case</Badge>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-muted rounded-lg">
            <p className="text-sm font-medium mb-1">Weekly Spending Limit</p>
            <p className="text-sm text-muted-foreground">
              Weekly total should not exceed $2,500 without manager review
            </p>
          </div>
        </CardContent>
      </Card>

      {/* AI Review Process */}
      <Card>
        <CardHeader>
          <CardTitle>AI-Powered Review Process</CardTitle>
          <CardDescription>
            How the system evaluates your expense submissions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold">
                1
              </div>
              <div>
                <p className="text-sm font-medium">Receipt Processing</p>
                <p className="text-xs text-muted-foreground">
                  PDF receipt is converted to images and analyzed using AI vision
                </p>
              </div>
            </div>
            
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold">
                2
              </div>
              <div>
                <p className="text-sm font-medium">Static Rules Check</p>
                <p className="text-xs text-muted-foreground">
                  Rules R1-R4 are applied based on amount, frequency, and receipt validity
                </p>
              </div>
            </div>
            
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold">
                3
              </div>
              <div>
                <p className="text-sm font-medium">Context Gathering</p>
                <p className="text-xs text-muted-foreground">
                  System retrieves policy documents, employee profile, and expense history as needed
                </p>
              </div>
            </div>
            
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold">
                4
              </div>
              <div>
                <p className="text-sm font-medium">Final Decision</p>
                <p className="text-xs text-muted-foreground">
                  AI agent makes final determination: APPROVE, REJECT, or MANUAL review
                </p>
              </div>
            </div>
            
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold">
                5
              </div>
              <div>
                <p className="text-sm font-medium">Payment Processing</p>
                <p className="text-xs text-muted-foreground">
                  Approved expenses are automatically added to your bank account balance
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Conflict Resolution */}
      <Card>
        <CardHeader>
          <CardTitle>Conflict Resolution</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            If the receipt contradicts the submitted metadata:
          </p>
          <ul className="text-sm space-y-2 ml-4 list-disc">
            <li>The receipt image is trusted as the primary source of truth</li>
            <li>The expense is flagged with rule &quot;CONFLICT&quot;</li>
            <li>Decision is set to MANUAL or REJECT depending on severity</li>
            <li>Specific conflicting fields are noted in the decision reason</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
