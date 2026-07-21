import { useQuery } from '@tanstack/react-query';
import { useSelector } from 'react-redux';
import { organizationsApi } from '@/services/organizations-api';
import type { RootState } from '@/store';

export function useOrganizations() {
  const { isAuthenticated, isHydrated } = useSelector((s: RootState) => s.auth);

  return useQuery({
    queryKey: ['organizations', isAuthenticated],
    queryFn: () => organizationsApi.list(),
    enabled: isHydrated && isAuthenticated,
  });
}
