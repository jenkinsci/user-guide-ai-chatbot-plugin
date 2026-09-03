# Quick Installation

This guide helps explain how to quickly setup the plugin to try it for the first time, skipping additional configurations.

### 1. Prerequisites

Before you begin, ensure you have the following installed on your system:
* **Git**
* **Python**
* **Docker**

### 2. Install the plugin on the Jenkins instance

Go in Manage Jenkins > Plugins > Available Plugins, search for "AI Chatbot to Guide User Workflow". Select it and click the button "Install". 

### 3. Clone the Repository

Open your terminal, navigate to the folder where you want to save the project, and run the following command:

```bash
git clone https://github.com/jenkinsci/user-guide-ai-chatbot-plugin
```

### 4. Navigate to the Project Directory

Change your current working directory to the newly cloned project folder:

```bash
cd user-guide-ai-chatbot-plugin
```

### 5. Build Frontend

Build the frontend project

```bash
cd frontend
npm run build
cd ../
```

### 6. Configure .env file

Create another copy of the .env.example file in the backend folder and name it .env.prod
Change the following vars:

```bash
########### JENKINS ############
JENKINS_URL="http://localhost:8080/jenkins" # Url of the jenkins instance
JWT_SECRET_KEY="your-secret-key"

########### AGENT ############
ROUTER_LLM_PROVIDER="groq"
ROUTER_LLM_MODEL_NAME = "llama-3.3-70b-versatile"
ROUTER_LLM_BASE_URL = "https://api.groq.com/openai/v1/"
ROUTER_LLM_API_KEY = "your-secret-key"

FINAL_LLM_PROVIDER="groq"
FINAL_LLM_MODEL_NAME = "llama-3.3-70b-versatile"
FINAL_LLM_BASE_URL = "https://api.groq.com/openai/v1/"
FINAL_LLM_API_KEY = "your-secret-key"

########### POSTGRESQL ############
POSTGRES_PASSWORD="your-secret-key"

############ QDRANT #############
QDRANT_SECRET_KEY="your-secret-key"

# ... rest unchanged
```

You can quickly generate a secret key with the following command: 
```bash
openssl rand -hex 32
```

### 7. Setup in Jenkins

Go in Manage Jenkins > System, scroll until you find the section "AI Chatbot Settings".

Set the following vars: 

**Backend URL** -> has to be the url of the FastAPI backend server, if hosted on the same machine set "http://127.0.0.1:8000/".

**API Key Credential** -> has to be the same value of the JWT_SECRET_KEY env var

### 8. Run the project

Execute the following command: 

```bash
python run.py prod
```

### 9. Restart Jenkins

Now restart Jenkins and you should be finally able to see the button to open chatbot panel at the bottom right of the screen.

![Open panel button](../../_static/images/ai-chatbot-button.png)


