import { RegisterForm } from '@/features/auth/components/register-form';

export const metadata = { title: 'Create account — Nexus PM' };

export default function RegisterPage() {
  return (
    <>
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-slate-100">Create account</h1>
        <p className="text-sm text-slate-400 mt-1">Start your free workspace</p>
      </div>
      <RegisterForm />
    </>
  );
}
