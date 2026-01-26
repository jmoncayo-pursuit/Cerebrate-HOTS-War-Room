# Quota Preservation Strategy

## 🎯 Goal: Minimize API Usage

You want to preserve your free quota and avoid unnecessary API calls.

## ✅ Changes Made

### 1. Ultra-Conservative Quota Limits
**File:** `quota_manager.py`

**New Limits:**
- `gemini-2.5-flash`: **50/day** (was 400, actual limit: 500)
- `gemini-3-pro`: **25/day** (was 200, actual limit: 250)
- `gemini-2.5-pro`: **15/day** (was 120, actual limit: 150)
- `gemini-1.5-flash`: **100/day** (was 800, actual limit: 1000)

**Impact:** System will stop making API calls after 50/day on primary model.

### 2. Replay Watcher Rate Limiting
**File:** `replay_watcher.py`

**Changes:**
- **Delay:** 4s → **30s** between replays (7.5x slower)
- **Batch Limit:** Max **20 new replays** per scan
- **Processing Rate:** ~120 replays/hour → ~2 replays/minute

**Impact:** 
- 500 replays would take **4+ hours** instead of 30 minutes
- Stops after 20 new replays to preserve quota
- Remaining replays processed on next scan

## 📊 Expected Usage

### Before Changes
- **Replay Backlog:** 500 replays × 1 API call = 500 calls in one session
- **Result:** Quota exhausted in hours

### After Changes
- **Per Session:** Max 20 replays × 1 API call = 20 calls
- **Per Day:** Max 50 API calls (hard limit)
- **Result:** Quota preserved, controlled usage

## 💰 Cost Impact

**Your Current Spend:** $7.78/month

**With Ultra-Conservative Limits:**
- Max 50 calls/day = ~1,500 calls/month
- Estimated cost: **$2-3/month** (60% reduction!)

## 🚀 Additional Recommendations

### 1. Disable Auto-Analysis (Optional)
Only analyze replays on-demand instead of automatically:
```python
# In replay_watcher.py, comment out the analysis trigger
# This would require manual analysis via UI
```

### 2. Use Local Recommendations First
The "Fast Path" system already does this - it returns local stats without API calls for simple queries like "Cursed Hollow draft".

### 3. Cache AI Responses
Implement response caching for repeated queries (not yet implemented).

### 4. Batch Analysis
Instead of analyzing each replay immediately, queue them and analyze in batches during off-hours.

## 🔧 How to Use

### Check Quota Status
```bash
curl http://localhost:8000/api/usage | jq '.quota'
```

### Manual Quota Reset (if needed)
```bash
rm .api_quota.json
```

### Process Replays Manually
Instead of auto-processing, you can manually trigger analysis:
```bash
# Process specific replay
curl -X POST http://localhost:8000/api/analyze_replay -F "file=@replay.StormReplay"
```

## 📝 Current State

**32 Failed Matches:**
- These need API calls to re-analyze
- At 50/day limit, you can safely retry them
- Cost: ~$0.50 total

**Recommendation:** 
- Retry the 32 failed matches (well within limits)
- Let the watcher process new replays slowly (20/session)
- Monitor quota via `/api/usage` endpoint

## ⚙️ Fine-Tuning

If 50/day is still too much, you can adjust:

**Even More Conservative:**
```python
# In quota_manager.py
DAILY_LIMITS = {
    "gemini-2.5-flash": 20,  # Only 20 calls/day
    ...
}
```

**Disable Watcher Auto-Processing:**
```bash
# Don't run replay_watcher.py automatically
# Only process replays manually when needed
```

## 🎯 Bottom Line

**Before:** Uncontrolled usage, 500+ calls in one session
**After:** Max 50 calls/day, 20 replays/session, predictable costs

Your quota is now protected!
