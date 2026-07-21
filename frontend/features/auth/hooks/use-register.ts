import { useMutation } from '@tanstack/react-query';
import { useDispatch } from 'react-redux';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { authApi, RegisterPayload } from '@/services/auth-api';
import { setCredentials } from '@/features/auth/store/auth-slice';

export function useRegister() {
  const dispatch = useDispatch();
  const router = useRouter();

  return useMutation({
    mutationFn: (payload: RegisterPayload) => authApi.register(payload),
    onSuccess: (data) => {
      dispatch(setCredentials(data));
      toast.success('Account created!');
      router.push('/dashboard');
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}
