'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSelector } from 'react-redux';
import type { RootState } from '@/store';

export function useAuthGuard() {
  const router = useRouter();
  const { isAuthenticated, isHydrated } = useSelector((s: RootState) => s.auth);

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isHydrated, isAuthenticated, router]);

  return isAuthenticated;
}
