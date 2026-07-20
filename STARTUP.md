# 🚀 PersonaVault Startup Guide

Follow these steps to correctly start the PersonaVault backend environment each time you enter Cloud Shell.

## 1. Navigate to the Project
Ensure you are in the backend root directory where the virtual environment is located.
```bash
cd /home/rajinderj8888/personavault/backend
```

## 2. Activate the Environment
Activate the Python virtual environment to load all required dependencies.
```bash
source .venv/bin/activate
```

## 3. Verify Prerequisites
Ensure your external services are running:
*   **Neo4j**: Must be accessible for graph operations.
*   **Ollama**: (Optional) Run `ollama serve` in a separate terminal if you are using local models.
*   **Environment**: Ensure your `.env` file contains valid `GEMINI_API_KEY` and database credentials.
*   **Permissions**: Ensure scripts are executable: `chmod +x *.sh`

## 4. Launch the API Server
Use the development restart script to launch the application. This script handles process cleanup and log redirection.
```bash
./dev_restart.sh
```

## 5. Access the Documentation
1. Click the **Web Preview** button in the top right of the Cloud Shell terminal.
2. Select **Preview on port 8080**.
3. Once the tab opens, add `/docs` to the end of the URL to access the interactive Swagger UI:
   `https://<your-preview-id>.cloudshell.dev/docs`

## 6. Default Credentials (Dev)
If you have just run `./dev_restart.sh`, the database has been wiped and re-seeded:
*   **URL**: `http://localhost:8000/admin/dashboard`
*   **User**: `admin`
*   **Pass**: `admin123`

---

## 🛠 Troubleshooting

### "Ran out of input" (Vector Index Error)
If the application fails to start with this error, the vector metadata was likely corrupted during a disk-full event. Fix it by deleting the corrupted file:
```bash
rm storage/vector_metadata.pkl
```

### Reclaiming Disk Space
If Cloud Shell warns you about 95% disk usage again, run these cleanup commands:
```bash
pip cache purge
rm -rf ~/.cargo/registry/src/*
```