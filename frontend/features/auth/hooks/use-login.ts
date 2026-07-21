import { useMutation } from '@tanstack/react-query';
import { useDispatch } from 'react-redux';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { authApi, LoginPayload } from '@/services/auth-api';
import { setCredentials } from '@/features/auth/store/auth-slice';

export function useLogin() {
  const dispatch = useDispatch();
  const router = useRouter();

  return useMutation({
    mutationFn: (payload: LoginPayload) => authApi.login(payload),
    onSuccess: (data) => {
      if ('requires2FA' in data && data.requires2FA) {
        sessionStorage.setItem('2fa_temp_token', data.tempToken);
        router.push('/login/2fa');
        return;
      }
      dispatch(setCredentials(data));
      toast.success('Welcome back!');
      router.push('/dashboard');
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}
