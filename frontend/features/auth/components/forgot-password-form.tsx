'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useForgotPassword } from '@/features/auth/hooks/use-forgot-password';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const { mutate: forgotPassword, isPending, isSuccess } = useForgotPassword();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    forgotPassword(email);
  }

  if (isSuccess) {
    return (
      <div className="text-center flex flex-col gap-4">
        <p className="text-slate-300 text-sm">
          If that email exists, a reset link is on its way.
        </p>
        <Link href="/login" className="text-indigo-400 hover:text-indigo-300 text-sm transition-colors">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="you@company.com"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={isPending}
        />
      </div>

      <Button
        type="submit"
        disabled={isPending}
        className="w-full bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white shadow-lg shadow-indigo-500/25 mt-1"
      >
        {isPending ? 'Sending…' : 'Send reset link'}
      </Button>

      <p className="text-center text-sm text-slate-400">
        Remembered it?{' '}
        <Link href="/login" className="text-indigo-400 hover:text-indigo-300 transition-colors">
          Sign in
        </Link>
      </p>
    </form>
  );
}
