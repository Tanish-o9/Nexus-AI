import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/services/projects-api';

export function useProject(id: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  });
}
