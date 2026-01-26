# Quota Exhaustion Analysis & Solution

## 🚨 Problem Identified

**Current Usage (from screenshot):**
- `gemini-2.5-flash`: **507/500 RPD** (101% - OVER LIMIT!)
- `gemini-3-pro`: **256/250 RPD** (102% - OVER LIMIT!)

**Root Cause:**
The replay watcher processes ALL replays on startup with only a 4-second delay between each one. If you have 500+ replays in your folder, it will:
1. Process all of them sequentially
2. Make 500+ API calls in a few hours
3. Exhaust your daily quota

**Why This Happened:**
- Line 575 in `replay_watcher.py`: `time.sleep(4)` - too short
- No daily quota tracking
- No batch size limits
- Processes entire backlog on every restart

## ✅ Solutions Implemented

### 1. QuotaManager Class (NEW)
Created `quota_manager.py` with:
- Daily quota tracking per model
- Conservative limits (80% of actual limits for safety)
- Automatic daily reset
- Persistent storage in `.api_quota.json`

**Limits Set:**
- `gemini-2.5-flash`: 400/day (actual: 500)
- `gemini-3-pro`: 200/day (actual: 250)
- `gemini-2.5-pro`: 120/day (actual: 150)
- `gemini-1.5-flash`: 800/day (actual: 1000)

### 2. Integration Points Needed

**A. API Server (`api_server.py`)**
- Import QuotaManager
- Check quota before each `call_gemini_api()` call
- Record usage after successful calls
- Return quota-aware errors

**B. Replay Watcher (`replay_watcher.py`)**
- Check quota before processing batch
- Stop processing when quota is low (< 50 remaining)
- Show quota status in terminal
- Resume next day automatically

### 3. User-Facing Features

**Check Quota Status:**
```bash
python3 -c "from quota_manager import QuotaManager; import json; print(json.dumps(QuotaManager().get_status(), indent=2))"
```

**Reset Quota (for testing):**
```bash
rm .api_quota.json
```

## 📊 Estimated Impact

**Before:**
- 500+ replays = 500+ API calls in one session
- Quota exhausted in hours
- No warning or protection

**After:**
- Max 400 calls per day (gemini-2.5-flash)
- Automatic stop at limit
- Resume next day
- Clear quota status

## 🎯 Next Steps

1. **Integrate QuotaManager into `api_server.py`**
   - Wrap `call_gemini_api()` with quota checks
   - Track model usage

2. **Update `replay_watcher.py`**
   - Check quota before batch processing
   - Show quota warnings

3. **Add UI Quota Display**
   - Show remaining quota in Services Panel
   - Warning when < 100 remaining

4. **Test with Retry Script**
   - The 32 failed matches will use ~32 API calls
   - Well within safe limits

## 💡 Recommendations

1. **Process replays in smaller batches** (50-100 at a time)
2. **Increase delay to 10 seconds** between API calls
3. **Use quota-aware retry script** for failed analyses
4. **Monitor quota daily** via UI or command

## 🔧 Quick Fix for Now

To prevent this from happening again immediately:

1. The QuotaManager is ready to use
2. Need to integrate it (requires code changes)
3. Alternative: Manually limit replay processing to 50/day

**Temporary Manual Fix:**
Only process the 32 failed matches (well within limits), then wait for quota reset tomorrow.
