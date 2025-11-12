"use client";

import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function Home() {
  const [count, setCount] = useState(0);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <main className="flex flex-col items-center gap-8 p-8">
        <div className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-foreground">
            Welcome to Your App
          </h1>
          <p className="text-lg text-muted-foreground">
            This is a simple example page built with Next.js and shadcn/ui
          </p>
        </div>
        
        <div className="flex flex-col items-center gap-4">
          <p className="text-2xl font-semibold text-foreground">
            Button clicked: {count} times
          </p>
          <Button 
            onClick={() => setCount(count + 1)}
            size="lg"
          >
            Click Me!
          </Button>
        </div>
      </main>
    </div>
  );
}
