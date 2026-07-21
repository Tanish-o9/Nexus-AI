import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { useSelector } from 'react-redux';
import { projectsApi, ProjectsParams } from '@/services/projects-api';
import type { RootState } from '@/store';

export function useProjects(params: ProjectsParams = {}) {
  const { isAuthenticated, isHydrated } = useSelector((s: RootState) => s.auth);
  const activeOrgId = useSelector((s: RootState) => s.org.activeOrgId);

  const queryParams: ProjectsParams = {
    ...params,
    organizationId: params.organizationId ?? (activeOrgId || undefined),
  };

  return useQuery({
    queryKey: ['projects', queryParams, isAuthenticated, activeOrgId],
    queryFn: () => projectsApi.list(queryParams),
    placeholderData: keepPreviousData,
    enabled: isHydrated && isAuthenticated,
  });
}
