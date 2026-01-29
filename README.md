# Newsroom 24/7 Automation

This bot automates the creation of viral news "Shorts" for the "Logic Vault" brand.
It fetches news, scripts it with a persona, generates audio/visuals, and (future) uploads to social media.

## 🚀 Setup & Usage (GitHub Actions)

This project is designed to run automatically on **GitHub Actions**.

### 1. Push Code

Push all files in this directory to your GitHub repository.

```bash
git init
git add .
git commit -m "Initial commit"
git push
```

### 2. Configure Secrets

Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
Add the following secrets:

- `NEWSDATA_API_KEY`: Your key from newsdata.io.
- `GEMINI_API_KEY`: Your Google Gemini API key.
- `TTS_API_KEY`: Your Play.ht or Cartesia API Key.
- `PEXELS_API_KEY`: Your Pexels API Key.
- `YOUTUBE_CREDS_JSON`: (Optical) Future YouTube credentials.

### 3. Run Workflow

- **Automatic**: Runs every 6 hours.
- **Manual**: Go to **Actions** tab -> **Newsroom 24/7 Bot** -> **Run workflow**.

### 4. Verify Output

- The workflow uploads the generated video as an **Artifact**.
- Go to the Workflow Run summary -> Scroll down to **Artifacts** -> Download `generated-videos`.

## 🛠 Local Development

1.  Install dependencies: `pip install -r requirements.txt`
2.  Install Playwright: `playwright install`
3.  Create `.env` file with your keys.
4.  Run: `python main.py`
