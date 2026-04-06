# Google Cloud Setup

This page walks through creating the OAuth credentials that gdsync needs to read your Google Drive.

## Step 1: Create a Google Cloud Project

1. Open [console.cloud.google.com](https://console.cloud.google.com) and sign in with your Google account.
1. In the top-left dropdown (next to "Google Cloud"), click **Select a project** then **New Project**.
1. Give it any name (e.g. "gdsync") and click **Create**.
1. Make sure the new project is selected in the top-left dropdown.

## Step 2: Enable the Google Drive API

1. In the left sidebar, go to **APIs & Services > Library**.
1. Search for **Google Drive API**.
1. Click on it, then click the blue **Enable** button.

## Step 3: Configure the OAuth Consent Screen

You must do this before creating credentials.

1. In the left sidebar, go to **APIs & Services > OAuth consent screen**.
1. Click **Get Started** (or **Configure Consent Screen**).
1. Fill in:
   - **App name**: anything (e.g. "gdsync")
   - **User support email**: your email
   - **Developer contact email**: your email
1. Click **Save and Continue** through each section (Scopes, Test Users, Summary) — defaults are fine.
1. On the **Test Users** step, click **Add Users** and add your own Gmail/Workspace email address, then continue.
1. You should see a summary page. Click **Back to Dashboard**.

> **Note:** While the app is in "Testing" status, only the test users you added can authorize it. This is fine for personal use.

## Step 4: Create OAuth Credentials

1. In the left sidebar, go to **APIs & Services > Credentials**.
1. Click **+ Create Credentials** at the top, then select **OAuth client ID**.
1. For **Application type**, choose **Desktop app**.
1. Name it anything (e.g. "gdsync Desktop").
1. Click **Create**.
1. A dialog appears with your client ID. Click **Download JSON**.
1. **Rename** the downloaded file to `credentials.json`.
1. **Move** it into place:

```bash
mkdir -p ~/.gdsync
mv ~/Downloads/client_secret_*.json ~/.gdsync/credentials.json
```

## Step 5: First run

```bash
gdsync --dry-run
```

1. A browser window will open asking you to sign in to Google.
1. You may see a warning: **"Google hasn't verified this app"** — this is expected for personal projects.
   - Click **Advanced** (bottom-left).
   - Click **Go to gdsync (unsafe)**.
1. Grant the requested permission (read-only access to Drive).
1. The browser will say "The authentication flow has completed." You can close it.

Your token is saved to `~/.gdsync/token.json` so you won't need to do this again.

## Security notes

- gdsync uses the `drive.readonly` scope. It **cannot** modify or delete your files.
- The OAuth token is stored with restricted file permissions (`0600`).
- Credentials never leave your machine.
