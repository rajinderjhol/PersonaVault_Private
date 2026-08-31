import { useQuery } from '@tanstack/react-query';
import { snowflakeService } from '../../services/snowflakeService';

export const useSnowflakeQuery = () => {
  return useQuery({
    queryKey: ['snowflakes'],
    queryFn: () => snowflakeService.getSnowflakes(),
    staleTime: 60000,
  });
};
