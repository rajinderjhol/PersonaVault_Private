import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const ingestionApi = {
  // Folder Ingestion
  ingestFolder: (folderPath: string, userId: number = 1, recursive: boolean = true) => 
    api.post('/api/v1/ingestion/folder', { folder_path: folderPath, user_id: userId, recursive }),
  
  // Job Status
  getJobStatus: (jobId: string) => 
    api.get(`/api/v1/ingestion/job/${jobId}`),

  // Supported Extensions
  getSupportedExtensions: () => 
    api.get('/api/v1/ingestion/supported-extensions'),
};

export default api;
