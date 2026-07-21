import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { authApi } from '@/services/auth-api';

export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) => authApi.forgotPassword(email),
    onSuccess: () => {
      toast.success('Password reset link sent — check your inbox.');
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}
