import { ForgotPasswordForm } from '@/features/auth/components/forgot-password-form';

export const metadata = { title: 'Reset password — Nexus PM' };

export default function ForgotPasswordPage() {
  return (
    <>
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-slate-100">Reset password</h1>
        <p className="text-sm text-slate-400 mt-1">We'll send a link to your inbox</p>
      </div>
      <ForgotPasswordForm />
    </>
  );
}
