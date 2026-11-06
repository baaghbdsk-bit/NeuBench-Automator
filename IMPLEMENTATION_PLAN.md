# NeuBench-Automator Safe Implementation Plan

## Design Overview (No Files Modified)

### Task A: Instagram
1. **Create menu selector fix**: Identify and fix mismatched CSS selector for Instagram Create menu. Works for both carousel and reel modes.
2. **Dedicated Instagram Reel action**: Add `instagram-reel` action choice in main.py argparse. Uses `reel:` identity prefix (already in post_history.json). Does not interfere with existing `carousel:` path.
3. **Preserve existing behavior**: Existing `instagram` action continues for carrousel; new `instagram-reel` is separate. Omnichannel behavior under `post-all` remains unchanged.

### Task B: YouTube Shorts
1. **Stable upload identity**: Use existing `stable_hash()` from platform_state.py. Format: `short:<sha256hash>` based on content metadata, not temporary paths. Complies with rule #7.
2. **Attach SRT captions**: After video rendering, locate associated `.srt` file (same base name). Pass to YouTube upload. Stores SRT path in platform history.
3. **Preserve existing functionality**: YouTube Shorts upload code path unchanged. SRT attachment is enhancement alongside existing logic.

### Task C: Pinterest
1. **Fix disabled title selector**: Add Playwright wait for media processing - `wait_for_selector` with `enabled=True` state, timeout 120s, graceful fallback. No changes to call sites or scheduling.

### Task D: Scheduling
1. **Instagram/YouTube Shorts workflow**: New workflow at `45 13 * * *` (19:15 Asia/Kolkata = 13:45 UTC). Uses concurrency group `neubench-instagram-youtube-shorts-${{github.run_id}}`. Explains GitHub Actions minute-level precision limitations. Includes idempotent state checks to handle heartbeat overlaps.
2. **Future long-form YouTube**: Designed for `45 11 * * 0/2` (17:15 Asia/Kolkata on alternate days). Not implemented in this plan.
3. **No collision with :00/:45 heartbeat**: Workflow is idempotent; state checks determine if Shorts already uploaded today. Concurrency groups prevent overlapping runs.
4. **State persistence after partial failures**: Each workflow persists state to post_history.json via platform_state.py. Failure on one platform never causes the other to repeat.

### Task E: Independent Upload Recovery - State Machine
**States per platform**: Generated → Approved → Upload pending → (YouTube published OR Instagram published) → Partially published / Fully published / Unknown upload outcome / Retry required

**Key principle**: Failure on one platform never causes already successful upload on other to be repeated.

**Implementation via platform_state.py** (design only):
- `reserve_platform_action` - atomic reservation with idempotency
- `complete_platform_action` - outcome tracking (success/unknown/failed)
- `is_platform_completed` - check if already published (skip if yes)
- `can_retry_platform` - determine if retry is appropriate

**Never retry conditions**: Platform state is `success` (already published). **Retry conditions**: State is `unknown` or `pending`.

### Concurrency Design
- New workflows use unique concurrency groups based on `github.run_id`
- Platform state via `post_history.json` with `atomic_write_json` and `x_history_lock`
- Failure isolation: Instagram failure does not affect YouTube state and vice versa

### Rollback Plan
1. Do NOT modify `.github/workflows/x_automater.yml` (primary boundary)
2. Revert any new workflow files
3. Revert `main.py` action changes if needed
4. Revert `platform_state.py` changes if needed
5. post_history.json state preserved; rollback doesn't affect historical data

### Test Coverage (design only)
- Unit tests for state machine functions
- Integration tests for dry-run mode
- Mock tests for selector fixes and SRT attachment
- Edge cases: mixed success/failure, second-run idempotency

### Strict Compliance
- ❌ Do NOT modify `.github/workflows/x_automater.yml`
- ❌ Do NOT touch LinkedIn, X, Bluesky, Threads
- ❌ Do NOT alter Pinterest call sites or scheduling
- ❌ Do NOT change existing schedules
- ❌ Do NOT execute any publishing
- ❌ Do NOT create or modify any files until explicit approval

---
*All designs respect: keeping x_automater.yml untouched, not modifying 4 protected platforms, preserving Pinterest call sites/scheduling, no execution until explicit approval.*