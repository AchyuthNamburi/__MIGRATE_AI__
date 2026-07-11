# 🚀 Migrate AI
**Autonomous Code Migration & Upgrading Agent**

Migrate AI is a powerful, multi-agent AI system designed to automatically analyze, plan, and execute framework migrations and codebase upgrades for existing GitHub repositories. 

It uses a resilient **Celery background task queue** combined with **FastAPI** to orchestrate multiple LLM agents (Discovery, Planning, Execution, and Verification) without timing out or blocking your browser.

---

## 🌐 Live Deployment
**Try it out here:** [https://migrate-ai-11f0.onrender.com](https://migrate-ai-11f0.onrender.com)

*(Note: Requires a GitHub account to login and import repositories).*

---

## ✨ Features
* **GitHub Integration:** One-click OAuth login and instant repository cloning.
* **Multi-Agent Pipeline:**
  * 🔍 **Discovery Agent:** Analyzes the codebase to detect the current framework, version, and dependencies.
  * 📋 **Planning Agent:** Formulates a step-by-step upgrade path based on detected versions.
  * ✍️ **Migration Agent:** Applies the actual code and dependency transformations.
  * 🧪 **Verification Agent:** Double-checks the changes for correctness.
* **Live Dashboard:** Real-time progress tracking of background AI tasks via Upstash Redis.
* **Resilient LLM Wrapping:** Built-in fallbacks across Groq, Gemini, and Mistral APIs to prevent rate-limiting failures.

---

## 📦 Supported Frameworks
Migrate AI is currently optimized for clean, single-framework repositories:
* **Django** (Python)
* **FastAPI** (Python)
* **Flask** (Python)
* **React** (JavaScript)
* **Pandas** (Data Science / Scripts)

*(Mixed framework repositories, such as Django+React tightly coupled in the same folder, may produce unpredictable results).*

---

## 🛠️ How to Use the Live App

1. **Login:** Go to the [Live App](https://migrate-ai-11f0.onrender.com) and click "Continue with GitHub".
2. **Import a Repo:** Click the **Import** button and paste a public GitHub `.git` URL.
   *(Example for testing: `https://github.com/ahfarmer/calculator.git`)*
3. **Migrate:** Click the **Migrate** button on the repository card.
4. **Wait & Watch:** The background Celery worker will take over. Watch the progress bar as the agents analyze, plan, and write the new code.
5. **Download:** Once it hits 100%, click the **Download** button to receive a `.zip` file containing your newly migrated codebase.

---

## 💻 Local Development Setup

To run this project on your own machine:

**1. Clone the repository:**
```bash
git clone https://github.com/AchyuthNamburi/__MIGRATE_AI__.git
cd __MIGRATE_AI__
```

**2. Set up the Python environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure Environment Variables:**
Create a `.env` file in the root directory. You will need:
* A PostgreSQL Database URL
* A Redis URL (for Celery)
* GitHub OAuth Client ID & Secret
* LLM API Keys (Groq, Google Gemini, Mistral)

**4. Start the Application:**
In terminal 1 (Start the Celery worker):
```bash
celery -A backend.workers.celery_app worker --loglevel=info
```

In terminal 2 (Start the FastAPI server):
```bash
uvicorn backend.main:app --reload
```

The app will now be running locally at `http://localhost:8000`.
