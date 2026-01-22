# Deploying to GitHub Pages

This project is configured to automatically update and deploy to GitHub Pages every 3 hours.

## Setup Instructions

### 1. Push your code to GitHub

```bash
git add .
git commit -m "Add GitHub Actions deployment workflow"
git push origin main
```

### 2. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages** (in the left sidebar)
3. Under "Build and deployment":
   - **Source**: Select "GitHub Actions"
4. Click **Save**

### 3. Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. If prompted, click "I understand my workflows, go ahead and enable them"
3. The workflow will run automatically on the schedule, or you can:
   - Click "Update Climbing Conditions Map" workflow
   - Click "Run workflow" to trigger it manually

### 4. View your live site

After the first successful run (takes ~2-3 minutes), your map will be available at:

```
https://<your-username>.github.io/<repository-name>/
```

For example: `https://murraycutforth.github.io/rime-predictor/`

## How It Works

The workflow (`.github/workflows/update-map.yml`) does the following:

1. **Triggers**: Runs every 3 hours, on push to main, or manually
2. **Fetches data**: Runs `python main.py` to generate the conditions map
3. **Commits**: Saves the generated `docs/index.html` to the repository
4. **Deploys**: Publishes the `docs/` directory to GitHub Pages

## Customization

### Change update frequency

Edit `.github/workflows/update-map.yml` and modify the cron schedule:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours instead of 3
```

Cron syntax: `minute hour day month weekday`
- `'0 */3 * * *'` = every 3 hours at :00
- `'0 8,20 * * *'` = twice daily at 8am and 8pm UTC
- `'0 6 * * *'` = once daily at 6am UTC

### Costs

- **GitHub Actions**: 2,000 free minutes/month for public repos (unlimited for public repos)
- **GitHub Pages**: Free for public repositories
- **Open-Meteo API**: Free tier (no API key required)

Total cost: **$0** for typical usage

## Troubleshooting

### Workflow fails on first run

If you see errors about missing dependencies, check:
1. `requirements.txt` is committed and up to date
2. GitHub Actions has write permissions (Settings → Actions → General → Workflow permissions → "Read and write permissions")

### Pages not deploying

1. Ensure GitHub Pages source is set to "GitHub Actions" (not "Deploy from a branch")
2. Check the Actions tab for any failed workflow runs
3. The first deployment can take 5-10 minutes to appear

### Map shows old data

The map updates every 3 hours automatically. To force an update:
1. Go to Actions tab
2. Click "Update Climbing Conditions Map"
3. Click "Run workflow" → "Run workflow"
