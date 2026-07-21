import { LoginForm } from '@/features/auth/components/login-form';

export const metadata = { title: 'Sign in — Nexus PM' };

export default function LoginPage() {
  return (
    <>
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-slate-100">Sign in</h1>
        <p className="text-sm text-slate-400 mt-1">Access your workspace</p>
      </div>
      <LoginForm />
    </>
  );
}
