import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const ingestionApi = {
  // Folder Ingestion
  ingestFolder: (folderPath: string, userId: number = 1, recursive: boolean = true) => 
    api.post('/ingestion/folder', { folder_path: folderPath, user_id: userId, recursive }),
  
  // Job Status
  getJobStatus: (jobId: string) => 
    api.get(`/ingestion/job/${jobId}`),

  // Supported Extensions
  getSupportedExtensions: () => 
    api.get('/ingestion/supported-extensions'),
};

export default api;
