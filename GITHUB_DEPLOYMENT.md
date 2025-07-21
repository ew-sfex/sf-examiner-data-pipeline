# 🚀 GitHub Actions Deployment Guide

**The Professional, Zero-Cost Solution for SF Examiner Data Pipeline**

## 🎯 Why GitHub Actions is Perfect

- ✅ **$0/month** - Completely free for public repos
- ✅ **Professional** - Used by millions of projects
- ✅ **Reliable** - 99.9% uptime SLA
- ✅ **Secure** - Built-in secrets management
- ✅ **Simple** - Just push code, it runs
- ✅ **Monitored** - Built-in logs and alerts

## 📋 Deployment Steps

### 1. Create GitHub Repository

```bash
# Create a new repository on GitHub.com
# Name it something like: sf-examiner-data-pipeline
```

### 2. Push Your Code

```bash
# In your project directory
git init
git add .
git commit -m "Initial commit: SF Examiner data pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sf-examiner-data-pipeline.git
git push -u origin main
```

### 3. Set Up Repository Secrets

Go to your repository on GitHub.com:

1. Click **Settings** tab
2. Click **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add these two secrets:

**Secret 1:**
- Name: `DATAWRAPPER_API_KEY`
- Value: `BVIPEwcGz4XlfLDxrzzpio0Fu9OBlgTSE8pYKNWxKF8lzxz89BHMI3zT1VWQrF2Y`

**Secret 2:**
- Name: `DATASF_APP_TOKEN`
- Value: `xdboBmIBQtjISZqIRYDWjKyxY`

### 4. Verify the Workflow

The workflow file is already included in `.github/workflows/update-charts.yml`

It will:
- ✅ Run daily at 3:00 AM UTC (11 PM PST / 10 PM PDT)
- ✅ Update all 25 visualizations
- ✅ Save logs for 30 days
- ✅ Allow manual triggering

### 5. Test the Setup

#### Option A: Manual Trigger (Recommended)
1. Go to **Actions** tab in your repository
2. Click **SF Examiner Data Pipeline**
3. Click **Run workflow** button
4. Watch it run and verify all steps pass

#### Option B: Wait for Scheduled Run
- It will automatically run at 3:00 AM UTC daily
- Check the **Actions** tab the next morning

## 📊 Monitoring & Management

### View Runs
- Go to **Actions** tab
- Click on any run to see detailed logs
- Download log files if needed

### Manual Triggering
- **Actions** tab → **SF Examiner Data Pipeline** → **Run workflow**
- Perfect for testing or urgent updates

### Scheduling
Current schedule: **Daily at 3:00 AM UTC**

To change timing, edit `.github/workflows/update-charts.yml`:
```yaml
schedule:
  - cron: '0 2 * * *'  # 2:00 AM UTC
  - cron: '0 */12 * * *'  # Every 12 hours
```

### Logs & Debugging
- All logs saved as "artifacts" for 30 days
- Download logs from any run in the Actions tab
- Individual script logs available

## 🔧 Customization Options

### Change Schedule
Edit the cron expression in the workflow file:
```yaml
schedule:
  - cron: '0 3 * * *'  # Daily at 3 AM UTC
```

### Add Email Notifications
Add this step to get email alerts on failures:
```yaml
- name: Send failure notification
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: "SF Examiner Pipeline Failed"
    body: "The data pipeline failed. Check GitHub Actions for details."
    to: your-email@example.com
```

### Run Only Specific Updates
Comment out steps you don't want:
```yaml
# - name: Run 311 Maps Update  # Disabled
#   run: python sf_311_maps.py
```

## 🛡️ Security Features

- ✅ **API keys stored as encrypted secrets**
- ✅ **No hardcoded credentials in code**
- ✅ **Isolated execution environment**
- ✅ **Audit trail of all runs**

## 🚨 Troubleshooting

### Common Issues

**Issue: Workflow doesn't run**
- Check the **Actions** tab is enabled in repository settings
- Verify the workflow file is in `.github/workflows/`

**Issue: API authentication failed**
- Check secrets are named exactly: `DATAWRAPPER_API_KEY` and `DATASF_APP_TOKEN`
- Verify secret values are correct (no extra spaces)

**Issue: Python dependencies fail**
- Check `requirements.txt` is in the root directory
- Verify all package names are correct

**Issue: Script fails**
- Download logs from the failed run
- Look for specific error messages
- Test scripts locally first

### Getting Help
1. Check the **Actions** tab for detailed error logs
2. Download artifact logs for full debugging info
3. Test individual scripts locally to isolate issues

## 🎉 Deployment Complete!

Once deployed, your pipeline will:

- ✅ **Run automatically** every night at 3 AM UTC
- ✅ **Update all 25 visualizations** with latest data
- ✅ **Cost $0/month** to operate
- ✅ **Provide professional monitoring** and logs
- ✅ **Handle failures gracefully** with detailed error reporting

Your SF Examiner data visualizations will stay fresh and current automatically! 

---

## 📈 Next Steps

1. **Test the deployment** with a manual workflow run
2. **Verify charts are updating** after the first automated run
3. **Set up email notifications** for failures (optional)
4. **Embed updated charts** on your website using Datawrapper URLs

The system is now fully professional, automated, and cost-effective! 🚀 