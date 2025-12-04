# Docker Setup for Ragatouille Project

This document provides instructions on how to build and run the Ragatouille backend (FastAPI) and frontend (Angular) applications using Docker and Docker Compose.

## Prerequisites

* Docker Desktop (or Docker Engine and Docker Compose) installed on your system.

## Project Structure

```
.
├── backend/                # FastAPI backend application
│   ├── Dockerfile          # Dockerfile for the backend
│   └── ...
├── frontend/               # Angular frontend application
│   ├── Dockerfile          # Dockerfile for the frontend
│   ├── nginx.conf          # Nginx configuration for the frontend
│   └── ...
└── docker-compose.yml      # Docker Compose configuration for both services
```

## Build and Run the Containers

1. **Navigate to the project root:**
   Open your terminal or command prompt and navigate to the root directory of the `ragatouille` project, where `docker-compose.yml` is located.

&nbsp;   ```bash
    cd C:\\Users\\rikha\\source\\ragatouille
    ```

2. **Build the Docker images:**
   This command will build the Docker images for both the backend and frontend services based on their respective `Dockerfile`s.

&nbsp;   ```bash
    docker-compose build
    ```

   * The backend image will be built from `backend/Dockerfile`.
   * The frontend image will be built from `frontend/Dockerfile`. During this build, the Angular application's API URL will be set to point to the backend service within the Docker network (`http://backend:8000`).

3. **Run the containers:**
   This command will start both the backend and frontend services in detached mode (in the background).

&nbsp;   ```bash
    docker-compose up -d
    ```

   * The FastAPI backend will be accessible externally on `http://localhost:4301`.
   * The Angular frontend will be accessible externally on `http://localhost:4300`.

4. **Check if the containers are running:**
   You can verify that both services are up and running using:

&nbsp;   ```bash
    docker-compose ps
    ```

   You should see output similar to this (names and ports might vary slightly):

   &nbsp;   ```
            Name                       Command               State           Ports
       -----------------------------------------------------------------------------------------
       ragatouille-backend-1   uvicorn app.main:app --host ... Up      0.0.0.0:8001->8000/tcp
       ragatouille-frontend-1  /docker-entrypoint.sh ngin... Up      0.0.0.0:80->80/tcp
       ```

   ## Accessing the Applications

* **Frontend:** Open your web browser and go to `http://localhost:80`.
* **Backend (FastMCP):** You can access the backend API (e.g., for API testing or MCP-specific endpoints) at `http://localhost:8001`.

  ## Stopping and Removing Containers

  To stop the running containers without removing them:

  ```bash
  docker-compose stop
  ```

  To stop and remove the containers, networks, and volumes defined in the `docker-compose.yml` file:

  ```bash
  docker-compose down
  ```

  ## Troubleshooting

* If you encounter issues, check the logs of individual services:

  &nbsp;   ```bash
      docker-compose logs <service\_name>
      ```

  (e.g., `docker-compose logs backend` or `docker-compose logs frontend`)

* Ensure that ports 80 and 8001 are not already in use by other applications on your host machine.
* If you make changes to the `Dockerfile`s or `docker-compose.yml`, you'll need to rebuild the images:

  &nbsp;   ```bash
      docker-compose build --no-cache
      docker-compose up -d
      ```

  This completes the setup for containerizing your Ragatouille project.

