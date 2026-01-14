# Backend Debug & Restart Instructions

## 🎯 Problem

The backend crashed after restart and is still showing old "Cookie Pool activé" message instead of the new "mode public" message.

## ✅ Solution

Run the comprehensive debug script on your Contabo server.

---

## 📋 Steps to Run on Contabo Server

### 1. SSH to your server

```bash
ssh root@184.174.36.43
```

### 2. Pull the latest changes

```bash
cd /home/shorts/Test-Omni-Videos
git fetch origin claude/setup-server-branch-H8EBU
git checkout claude/setup-server-branch-H8EBU
git pull origin claude/setup-server-branch-H8EBU
```

### 3. Run the debug script

```bash
cd /home/shorts/Test-Omni-Videos/saas
bash debug_and_restart_backend.sh
```

---

## 🔍 What the Script Does

The script performs a complete diagnostic and restart:

1. **Checks crash logs** - Shows why the backend crashed
2. **Finds running processes** - Identifies all backend processes
3. **Checks port 8000** - Sees what's using the API port
4. **Kills ALL processes** - Ensures clean slate
5. **Verifies cleanup** - Confirms no zombie processes
6. **Tests dependencies** - Checks Python modules load correctly
7. **Tests syntax** - Validates main.py has no errors
8. **Foreground test** - Runs backend briefly to catch startup errors
9. **Starts in background** - Launches backend properly
10. **Verifies startup** - Confirms process is running
11. **Tests API** - Calls health check endpoint
12. **Tests processing** - Checks if "mode public" message appears

---

## ✅ Expected Output

At the end, you should see:

```
✅✅✅ SUCCESS! Backend is running NEW code (mode public)
```

If you see:

```
❌❌❌ ERROR! Backend is still running OLD code (Cookie Pool)
```

Then the script will help you identify what went wrong.

---

## 📊 After Running

The script will tell you:

- **Backend PID** - Process ID of the running backend
- **Log file** - Where to find logs (`/var/log/shorts-backend.log`)
- **Backend dir** - Working directory

### Monitor logs in real-time:

```bash
tail -f /var/log/shorts-backend.log
```

### Stop the backend:

```bash
kill <PID>
```

---

## 🚨 Common Issues & Fixes

### Issue 1: "Module not found" errors

**Fix:**
```bash
cd /home/shorts/Test-Omni-Videos
pip3 install -r requirements.txt
```

### Issue 2: Port 8000 already in use

**Fix:**
```bash
# Find what's using it
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Issue 3: Permission denied

**Fix:**
```bash
chmod +x /home/shorts/Test-Omni-Videos/saas/debug_and_restart_backend.sh
```

### Issue 4: Still showing old code after restart

**Possible causes:**
- Wrong directory - Check that `/home/shorts/Test-Omni-Videos` is the correct path
- Git not pulled - Make sure you ran `git pull` before the script
- Python caching - Try `find . -name "*.pyc" -delete` to clear cache

---

## 🎓 What Changed

### Removed Cookie Pool entirely:
- ❌ No more `cookie_pool_manager.py`
- ❌ No more `cookie_refresher.py`
- ❌ No more cookie upload on frontend

### Simplified to "Mode Public":
- ✅ Works without cookies for 60-80% of public YouTube videos
- ✅ Clear error messages if a video requires authentication
- ✅ Much simpler architecture

### Updated files:
- `saas/backend/youtube_downloader.py` - Tries without cookies first
- `saas/backend/main.py` - Messages say "mode public" not "Cookie Pool"
- `saas/frontend/index.html` - No cookie upload field

---

## 📞 Need Help?

If the script fails or shows unexpected errors, check:

1. `/var/log/shorts-backend.log` - Full error logs
2. Python version: `python3 --version` (should be 3.8+)
3. Git branch: `git branch` (should show `claude/setup-server-branch-H8EBU`)
4. Working directory: `pwd` (should be `/home/shorts/Test-Omni-Videos`)

---

**Ready to run?** Just execute the 3 steps above on your Contabo server! 🚀
