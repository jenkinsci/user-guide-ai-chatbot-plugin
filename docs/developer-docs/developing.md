# Development Guide

This document explains the commands needed to launch the development environment according to your needs.

## Full-Stack Development (Complete Plugin)
If you want to develop or test the plugin in its entirety, you need to start both the main process and the backend.

1. From the terminal, in the **main (root) folder**, compile and start the base process:
```bash
# Clean the project and run the HPI plugin
mvn install
mvn clean hpi:run
```

2. In a **second terminal**, start the backend in Python:
```bash
# Navigate to the backend folder and start the dev server
cd backend
python run.py install
python run.py dev
```

## 🎨 Frontend Development (UI Only)
If your work focuses exclusively on improving the user interface, simply start the local frontend server.

```bash
# Navigate to the frontend directory and start the UI dev server
cd frontend
npm install
npm run dev
```