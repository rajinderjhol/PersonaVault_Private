import { api } from './api';

export const snowflakeService = {
  getSnowflakes: () => api.get('/thermodynamics/snowflakes'),
};
