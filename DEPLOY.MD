# Deploying metabolicai

This guide will help you deploy **metabolicai** to popular cloud platforms and run it in production environments. These instructions assume you have basic familiarity with the platform you choose.

---

## 💻 Local (for quick testing)

1. Clone the repo & set up environment variables:

   ```bash
   git clone https://github.com/furqanagwan/metabolicai.git
   cd metabolicai
   cp .env.example .env
   # (edit .env if needed)
   ```

2. Run via Docker Compose (recommended):

   ```bash
   docker-compose up --build
   ```

   * The API will be available at [http://localhost:8000](http://localhost:8000)
   * Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

3. Or run locally:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

---

## 🔑 Register a User Before Logging Data

Before you can log entries or get predictions, **register a user profile**:

```bash
curl -X POST "http://localhost:8000/user" \
  -H "X-API-Key: yourapikey" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo", "age": 30, "gender": "male"}'
```

After this, you can log entries with `POST /entry` or `PATCH /entry` as usual.

---

## ☁️ Deploy to Azure Machine Learning (AMLS)

1. **Containerize**: The provided `Dockerfile` builds a portable container image for metabolicai.
2. **Push to Azure Container Registry** (optional but recommended):

   * Build the image:

     ```bash
     az acr build --registry <your-acr-name> --image metabolicai:latest .
     ```
   * Or build and push locally:

     ```bash
     docker build -t <acr-name>.azurecr.io/metabolicai:latest .
     docker push <acr-name>.azurecr.io/metabolicai:latest
     ```
3. **Deploy on Azure ML**:

   * Use Azure ML Studio > Endpoints > Create Online Endpoint
   * Choose custom Docker image and enter your registry path (`<acr-name>.azurecr.io/metabolicai:latest`)
   * Set environment variables in the Azure UI (from your `.env`)
   * Finish deployment and test via the public endpoint

> **Reminder:** Register a user profile as above before logging entries!

---

## ☁️ Deploy to AWS SageMaker

1. **ECR Build & Push:**

   * Build Docker image:

     ```bash
     docker build -t metabolicai .
     aws ecr create-repository --repository-name metabolicai
     docker tag metabolicai:latest <aws-account-id>.dkr.ecr.<region>.amazonaws.com/metabolicai:latest
     aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com
     docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/metabolicai:latest
     ```
2. **Deploy Model:**

   * Use SageMaker Studio or CLI to create an Endpoint using your image
   * Configure environment variables and networking as needed
   * Deploy and test

> **Reminder:** Register a user profile as above before logging entries!

---

## ☁️ Deploy to Google Cloud Vertex AI

1. **Build & Push to Artifact Registry:**

   * Build image and push:

     ```bash
     gcloud builds submit --tag <region>-docker.pkg.dev/<project-id>/metabolicai/metabolicai:latest .
     ```
2. **Deploy on Vertex AI:**

   * Go to Vertex AI > Endpoints > Create Endpoint
   * Select Custom Container and use your pushed image
   * Set environment variables
   * Deploy and test

> **Reminder:** Register a user profile as above before logging entries!

---

## 🌍 Public Cloud/VM (Generic Ubuntu, DigitalOcean, etc)

1. Provision a VM (Ubuntu recommended)
2. Install Docker & Docker Compose

   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose
   ```
3. Clone the repo, set env vars, and run:

   ```bash
   git clone https://github.com/furqanagwan/metabolicai.git
   cd metabolicai
   cp .env.example .env
   docker-compose up --build -d
   ```
4. Configure your firewall to allow access to port 8000
5. API is now accessible on your server’s public IP!

> **Reminder:** Register a user profile as above before logging entries!

---

## 🔒 Production Best Practices

* Use strong API keys and never expose your real `.env` publicly
* Set up HTTPS (via a reverse proxy like nginx or Caddy, or use cloud platform HTTPS features)
* Monitor logs and configure automatic restarts (e.g. Docker restart policies)
* Use managed DB/file storage for scale (optional)

---

## 🙋 Need help?

Open an issue or [connect on LinkedIn](https://linkedin.com/in/furqanagwan). Contributions and questions are always welcome!
