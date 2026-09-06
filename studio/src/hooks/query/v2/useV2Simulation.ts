import { useMutation } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export const useV2RunSimulation = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useMutation({
    mutationFn: async (params: any) => {
      if (!currentEnvId) throw new Error('No environment selected');
      // Note: The audit showed the endpoint as /simulation/run, 
      // but the path here should be consistent with how environments work.
      // Based on the router, it seems like environments might be top-level.
      // Let's use the path as defined in the router: /simulation/run
      const response = await v2ApiClient.post(
        `/simulation/run`,
        params
      );
      return response;
    },
  });
};
