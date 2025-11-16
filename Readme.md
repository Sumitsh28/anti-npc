# 🤖 Anti-NPC: AI-Powered Contributor Analysis Bot

**Anti-NPC** is an intelligent GitHub App that serves as a powerful assistant for maintainers. Instead of just counting commits, this bot uses Generative AI to perform a deep analysis of a user's _actual_ contributions and skills, flagging low-effort "NPC" comments and highlighting high-quality contributors.

It analyzes every user comment on an issue, generates a detailed fitness score, and provides actionable feedback directly in the issue thread.

---

## 🚀 Features

- **🧠 Deep Contribution Analysis:** The bot fetches the _code diffs_ of a user's past merged PRs in the repo and uses an LLM to score their _complexity_—separating typo fixes from new features.
- **🎯 Context-Aware Skill Matching:** It analyzes the issue's title, body, and **labels** (e.g., `frontend`, `database`) to determine the required tech stack.
- **📈 Holistic User Profiling:** It builds a skill profile for the user by analyzing their GitHub bio, their comment's explanation quality, and the languages of their other public repositories.
- **💬 Actionable & Dynamic Feedback:** The bot's response changes based on the final score:
  - **High Score:** Praises the user and notifies the maintainer of a great match.
  - **Medium Score:** Provides constructive feedback (e.g., "Your profile looks good, but can you provide a plan?").
  - **Low Score (Spam Flag):** Flags low-effort, no-context requests to the maintainer as "Low-Effort" or potential "NPC" behavior.
- **⚡ Intelligent Caching:** Expensive user-profile analysis (like PR diffs and repo languages) is cached using a 72-hour **TTLCache** to reduce API costs and latency for repeat commenters.

---

## ⚙️ Architectural Flow

The entire process is event-driven, orchestrated by the Flask server.

1.  **Webhook Ingestion:** A user comments on an issue. GitHub fires an `issue_comment` webhook, which is sent to the app's `/webhook` endpoint.
2.  **Signature Verification:** The server validates the request's `X-Hub-Signature-256` to ensure it's from GitHub.
3.  **Authentication:** `github_helper.py` generates a short-lived **JWT (JSON Web Token)** using the app's private key. This JWT is exchanged with GitHub's API for a temporary **Installation Access Token**.
4.  **Client Initialization:** The token is used to initialize a `PyGithub` client, which can now act as the bot for that specific repository.
5.  **Caching Layer:** The `commenter_username` is checked against the `TTLCache` in `cache_helper.py`.
    - **Cache Hit:** The user's `user_data` and `contribution_analysis` are retrieved instantly.
    - **Cache Miss:** The bot proceeds to the expensive fetching steps.
6.  **Multi-Stage Data Fetching (Cache Miss):**
    - `get_user_data()`: Fetches the user's bio, public repo languages, and—most importantly—the `diff_url`s for their last 3 merged PRs in _this_ repo.
    - `requests` is used to download the raw PR diffs from these URLs.
7.  **Multi-Stage AI Analysis:**
    - `analyze_issue_and_repo()`: The issue's body, labels, and the repo's README are sent to OpenAI to extract the required `tech_stack`.
    - `analyze_user()`: The user's bio, repo languages, and their _new comment_ are sent to analyze their `user_skills` and `explanation_quality`.
    - `analyze_contribution_quality()`: The raw PR diffs are sent to score their average `average_complexity` (from 1-10).
8.  **Cache Population:** The results of the expensive user analysis (`user_data` and `contribution_analysis`) are stored in the `TTLCache` for 72 hours.
9.  **Scoring & Report Generation:**
    - `scoring.py` receives the structured JSON from all AI calls.
    - It maps the AI scores (e.g., `average_complexity` 1-10) to weighted score components (e.g., `repo_contributions` 0-2).
    - A **dynamic, actionable report** is generated based on the final score.
10. **API Response:** The `PyGithub` client posts the final Markdown report as a new comment on the issue.

---

## 🛠️ Tech Stack

- **Backend:** **Flask** (for the webhook server)
- **GitHub Integration:** **PyGithub** (for API interaction), **PyJWT** (for authentication)
- **AI / LLM:** **OpenAI** (using `gpt-4o-mini` for analysis)
- **Caching:** **cachetools** (for in-memory TTL caching)
- **HTTP & Utils:** **requests**, **python-dotenv**

---

## 📸 Screenshot

![alt text](https://raw.githubusercontent.com/Sumitsh28/images/710a851af43bb2b890834b27063e184a0b438048/before.png)
![alt text](https://raw.githubusercontent.com/Sumitsh28/images/710a851af43bb2b890834b27063e184a0b438048/after.png)

---

## 📚 Setup & Local Development

Follow these steps to run the bot on your local machine for testing.

### 1. Create the GitHub App

1.  Go to **GitHub Settings** > **Developer settings** > **GitHub Apps** > **New GitHub App**.
2.  **App Name:** "Anti-NPC Bot" (or your choice).
3.  **Homepage URL:** `https://github.com`
4.  **Webhook:**
    - Check **Active**.
    - **Webhook URL:** You'll get this from `ngrok` in a later step. For now, use a placeholder like `http://example.com`.
    - **Webhook secret:** Generate a strong, random string (e.g., with a password manager) and save it.
5.  **Repository Permissions:**
    - **Contents:** `Read-only` (To read READMEs)
    - **Issues:** `Read & write` (To read issues and post comments)
    - **Pull Requests:** `Read-only` (To read PR diffs)
6.  **Subscribe to events:**
    - Check **Issue comment**.
7.  Click **Create GitHub App**.
8.  On the app's page, generate a **private key** and download the `.pem` file.

### 2. Configure Your Local Environment

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/your-username/anti-npc.git](https://github.com/your-username/anti-npc.git)
    cd anti-npc
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Create your `.env` file:**

    - Copy `.env.example` to `.env`.
    - Place the downloaded `.pem` file into your project folder.
    - Fill in the `.env` file with your keys:

    ```ini
    # 1. GitHub App Settings
    GITHUB_APP_ID="YOUR_APP_ID"             # From your app's "General" page
    GITHUB_WEBHOOK_SECRET="YOUR_WEBHOOK_SECRET" # The secret you created

    # 2. GitHub App Private Key
    GITHUB_PRIVATE_KEY_PATH="./your-app-name.private-key.pem" # The path to your .pem file

    # 3. OpenAI API Key
    OPENAI_API_KEY="sk-..."
    ```

### 3. Run the Server

1.  **Run the Flask app:** (The code is set to run on port 5001)

    ```bash
    python main.py
    ```

2.  **Expose your local server with `ngrok`:**

    ```bash
    ngrok http 5001
    ```

    `ngrok` will give you a public `https://...ngrok.io` URL. Copy it.

3.  **Update your GitHub App:**
    - Go back to your GitHub App's settings.
    - Set the **Webhook URL** to your `ngrok` URL (e.g., `https://<hash>.ngrok.io/webhook`).
    - Save changes.

### 4. Install and Test

1.  Go to your app's "Install App" tab and install it on a test repository.
2.  Go to that repository, create an issue, and post a comment.
3.  Watch your `python main.py` terminal! You will see the bot spring to life, fetch all the data, and post its analysis.

---

## 🚀 Deployment

For production, do not use `ngrok`. Deploy the Flask application to a persistent server (e.g., Heroku, Render, AWS EC2, or Vercel).

- **Important:** Do not commit your `.pem` file. On your production server, store the _contents_ of the `.pem` file in a secure environment variable. You will need to modify `github_helper.py` to read the key from `os.environ.get('GITHUB_PRIVATE_KEY')` instead of a file.

---

## LICENSE

[MIT](LICENSE)
