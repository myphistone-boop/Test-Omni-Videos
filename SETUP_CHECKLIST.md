# 🚀 Setup Checklist - YouTube Upload Module

## Current Status: OAuth Authentication Pending

### ✅ Completed Steps
- [x] YouTube upload module created (youtube_upload/)
- [x] OAuth 2.0 Client ID created in Google Cloud Console
- [x] OAuth consent screen (branding) configured
- [x] client_secrets JSON downloaded from Google Cloud

### 📋 Next Steps (Complete in Order)

#### Step 1: Place client_secrets.json file
```bash
# The file should be at the PROJECT ROOT (not in youtube_upload/)
# Location: /home/user/Test-Omni-Videos/client_secrets.json

# From Windows:
# C:\Users\jferreira\Dev-repo-JFE\Omni-videos\client_secrets.json
```

**How to verify:**
```bash
ls -la /home/user/Test-Omni-Videos/client_secrets.json
```

---

#### Step 2: Add Test User in Google Cloud Console

1. Go to: https://console.cloud.google.com/
2. Select your project ("YouTube Automation" or similar)
3. Navigate to: **APIs & Services** → **OAuth consent screen**
4. Scroll down to **"Test users"** section
5. Click **"+ ADD USERS"**
6. Add the email address of your YouTube account
7. Click **Save**

**⚠️ Important:** Use the SAME email as the YouTube channel you want to upload to!

---

#### Step 3: Authenticate Your Account

```bash
cd youtube_upload
python youtube_auth.py --account compte_test_1
```

**What will happen:**
1. Browser window opens
2. You'll see a warning: "Google hasn't verified this app"
3. Click **"Advanced"** → **"Go to [Your App Name] (unsafe)"**
4. Log in with your YouTube account (the one you added as test user)
5. Click **"Allow"** to grant upload permissions
6. Window closes automatically
7. You'll see: ✅ Authentification réussie pour compte_test_1

**Verification:**
```bash
python youtube_auth.py --list
```
Should show: ✅ compte_test_1

---

#### Step 4: Test Upload (Dry Run)

Create a simple test video first:
```bash
# Create a 10-second test video
ffmpeg -f lavfi -i color=c=blue:s=1080x1920:d=10 -vf "drawtext=text='TEST VIDEO':fontsize=100:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" test_video.mp4
```

Then test the upload:
```bash
cd youtube_upload
python youtube_uploader.py \
  --video ../test_video.mp4 \
  --title "Test Short Video" \
  --account compte_test_1
```

**Expected output:**
```
🔐 Connexion au compte: compte_test_1
✅ Compte connecté: [Your Channel Name]

📊 Métadonnées générées:
Titre: [Auto-generated unique title]
Description: [Auto-generated description]
Tags: [Auto-generated tags]

📤 Upload en cours...
[Progress bar showing upload]

✅ Vidéo uploadée avec succès !
📺 URL du Short: https://www.youtube.com/shorts/[VIDEO_ID]
```

---

## 🎯 After Successful Test

Once you've successfully uploaded a test video:

1. **Verify on YouTube:**
   - Go to YouTube Studio: https://studio.youtube.com
   - Check that the video appears
   - Verify metadata (title, description, tags)

2. **Delete test video:**
   - In YouTube Studio, delete the test video
   - Clean up: `rm ../test_video.mp4`

3. **Ready for production:**
   - You can now integrate the upload module with your main pipeline
   - Scale to additional accounts when ready

---

## 🔧 Troubleshooting

### Error: "client_secrets.json not found"
→ Make sure file is at project root: `/home/user/Test-Omni-Videos/client_secrets.json`

### Error: "403: access_denied"
→ Add your email to Test Users in Google Cloud Console (Step 2)

### Error: "The user has not granted the app..."
→ Re-run authentication: `python youtube_auth.py --account compte_test_1`

### Browser doesn't open during auth
→ Check firewall settings or manually copy the URL from terminal

---

## 📞 Quick Commands Reference

```bash
# List authenticated accounts
python youtube_auth.py --list

# Re-authenticate an account
python youtube_auth.py --account compte_test_1

# Upload a video
python youtube_uploader.py --video PATH --title "TITLE" --account ACCOUNT_ID

# Test the full pipeline (discover + process + upload)
cd ..
python main_pipeline.py  # (Coming soon: integration)
```

---

## 🎬 Next Steps After This Works

1. ✅ Test with 1 account (compte_test_1)
2. Validate for 1 week
3. Scale to 5 accounts (3 FR + 2 EN)
4. Scale to 10 accounts (5 FR + 5 EN)
5. Integrate with main pipeline automation
6. Add scheduler for daily uploads
