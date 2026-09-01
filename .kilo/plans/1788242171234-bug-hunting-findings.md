# Bug Hunting Findings

## Summary
Inspected the DWRMS codebase (backend FastAPI + frontend Next.js) and identified 8 confirmed bugs across idempotency, SLA evaluation, request fulfillment, setup wizard, network resilience, and frontend data loading.

---

## Bug 1: Idempotency middleware caches client errors (4xx)

**File:** `backend/app/core/idempotency.py:80`

**Problem:**
```python
if response.status_code < 500:
    # caches 2xx, 3xx, AND 4xx responses
```
The middleware caches ALL non-5xx responses, including 4xx client errors (400, 409, 422). This means a duplicate submission with invalid data gets cached and silently replayed on retry instead of re-validated.

**Impact:** Users see stale 400/409 errors on retry; legitimate fixes to request payloads are ignored because the cached error is replayed.

**Fix:** Change the condition to cache only successful responses:
```python
if response.status_code < 300:
```

**Edge case:** 3xx redirects should also not be cached, as they are context-dependent.

---

## Bug 2: Network timeout error message mismatch

**File:** `frontend/src/lib/networkResilience.ts:131, 184`

**Problem:**
- Line 131: `signal: AbortSignal.timeout(4000)` — heartbeat probe timeout is **4 seconds**
- Line 184: Error message says `"timed out after 10 seconds"`

**Cross-reference:** `frontend/src/lib/api.ts:93` uses `setTimeout(..., 10000)` for general API calls with the comment `// 10s default timeout`. The 10s message in networkResilience.ts appears to be a copy-paste error from the general API fetch logic.

**Impact:** User-facing error message is misleading; operators debug the wrong timeout value.

**Recommendation:** Update line 184 to say `"timed out after 4 seconds"`. The 4s timeout is appropriate for fast-fail heartbeat probes. If a longer timeout is desired for health checks, change the AbortSignal.timeout value instead and keep the message in sync.

**Fix:**
```typescript
return `Server response timed out after 4 seconds. The central server may be busy or unreachable.`;
```

---

## Bug 3: Setup wizard advances on save failure

**File:** `frontend/src/app/setup/SetupClient.tsx:200-211`

**Problem:**
```typescript
try {
    setLoading(true);
    await apiClient.post(`/setup/step/${currentStep}`, { step_data: formData });
    setCurrentStep((prev) => Math.min(prev + 1, 8));
} catch (err) {
    // Continue anyway for local testing
    setCurrentStep((prev) => Math.min(prev + 1, 8));
}
```
When the backend fails to save a step, the frontend still advances to the next step.

**Impact:** Setup progress is lost silently; user sees later steps but configuration isn't persisted. Finalization will fail or produce an incomplete setup.

**Fix:** Do not advance the step on failure. Show the error and let the user retry:
```typescript
} catch (err) {
    setStatusMessage({ type: 'error', text: 'Failed to save step. Please retry.' });
    return;
}
```

**Note:** The "local testing" comment suggests this was intentional for offline development, but it creates a silent data loss bug in production use.

---

## Bug 4: Redundant catalog API call in Materials page

**File:** `frontend/src/app/materials/page.tsx:129, 138`

**Problem:**
```typescript
if (activeTab === 'REQUIREMENTS') {
    // ... fetch requirements
} else {
    let url = `/api/v1/materials/catalog?limit=100`;  // line 129
    // ... fetch catalog
}
const catData = await apiFetch<CatalogItem[]>('/api/v1/materials/catalog?limit=200'); // line 138
```
Catalog is fetched unconditionally at line 138 regardless of active tab, after already being fetched at line 129 when the catalog tab is active.

**Impact:** Double API call on catalog tab; unnecessary bandwidth and latency.

**Fix:** Remove line 138 or guard it with `if (activeTab === 'CATALOG')`.

---

## Bug 5: SLA completion breach overwrites response breach

**File:** `backend/app/modules/sla/service.py:644-651`

**Problem:**
```python
if now > target_comp_utc:
    if tracker.health != SLAHealth.BREACHED_RESPONSE.value:
        tracker.health = SLAHealth.BREACHED_COMPLETION.value
    elif tracker.health == SLAHealth.BREACHED_RESPONSE.value:
        tracker.health = SLAHealth.BREACHED_COMPLETION.value  # BUG: overwrites higher severity
```
The comment on line 648 says "If response was already breached, keep BREACHED_RESPONSE (higher severity captured first)" but the `elif` branch **overwrites** it with `BREACHED_COMPLETION`.

**Impact:** SLA health severity is downgraded from `BREACHED_RESPONSE` to `BREACHED_COMPLETION` when both deadlines are missed, contradicting the documented intent that response breach is the higher-severity captured state. This affects escalation routing and dashboard severity coloring.

**Fix:** Remove the `elif` branch or change it to `pass` to preserve `BREACHED_RESPONSE`:
```python
if now > target_comp_utc:
    if tracker.health != SLAHealth.BREACHED_RESPONSE.value:
        tracker.health = SLAHealth.BREACHED_COMPLETION.value
    # else: keep BREACHED_RESPONSE (higher severity, already captured)
```

---

## Bug 6: Request fulfillment allows re-fulfilling completed requests

**File:** `backend/app/modules/requests/service.py:363`

**Problem:**
```python
if req.status != "APPROVED" and req.fulfillment_status not in ["AWAITING_FULFILLMENT", "PARTIALLY_FULFILLED"]:
    raise HTTPException(status_code=400, detail="Request must be APPROVED before fulfillment")
```
Uses `and` instead of `or`. When a request transitions to `APPROVED` status but its `fulfillment_status` is already `FULFILLED` (e.g., from a prior fulfillment call that set both fields), the first condition (`req.status != "APPROVED"`) is `False`, which short-circuits the `and` to `False`, allowing the re-fulfillment to proceed.

**Truth table for the bug:**
| req.status | req.fulfillment_status | status != APPROVED | status not in list | and result | Correct? |
|---|---|---|---|---|---|
| APPROVED | AWAITING_FULFILLMENT | False | False | False | Allowed ✓ |
| APPROVED | FULFILLED | False | True | **False** | **Blocked incorrectly** |
| FULFILLED | FULFILLED | True | True | True | Blocked ✓ |

**Impact:** A request that was already fulfilled can be re-fulfilled, potentially creating duplicate fulfillment logs, triggering unnecessary notifications, or corrupting financial tracking (`actual_cost` updates).

**Fix:** Use `or` so that EITHER invalid condition triggers rejection:
```python
if req.status != "APPROVED" or req.fulfillment_status not in ["AWAITING_FULFILLMENT", "PARTIALLY_FULFILLED"]:
    raise HTTPException(status_code=400, detail="Request must be APPROVED before fulfillment")
```

---

## Bug 7: Missing null check after re-query in material issue

**File:** `backend/app/modules/requests/service.py:414-415`

**Problem:**
```python
req_res = await db.execute(select(OperationalRequest).where(OperationalRequest.id == request_id))
req = req_res.scalar_one()  # No null check
```
Uses `scalar_one()` which raises `NoResultFound` if the request was deleted between the initial fetch and this re-query.

**Impact:** Unhandled `NoResultFound` exception (500 error) on concurrent deletion, instead of a clean 404.

**Fix:** Use `scalar_one_or_none()` and raise a proper 404:
```python
req = req_res.scalar_one_or_none()
if not req:
    raise HTTPException(status_code=404, detail="Request not found")
```

---

## Bug 8: Frontend default DB engine mismatch with docker-compose

**File:** `frontend/src/app/setup/SetupClient.tsx:64` and `docker-compose.yml:5-10`

**Problem:**
- Setup wizard defaults to `db_engine: 'mysql'` (line 64)
- `docker-compose.yml` uses PostgreSQL (`postgres:16`, port 5432)

**Impact:** First-time users setting up via the wizard are misled into configuring MySQL when the containerized environment is PostgreSQL. This causes connection failures during setup finalization.

**Fix:** Change the default in `SetupClient.tsx` to `'postgresql'` to match the docker-compose default. Also update the select option ordering to put PostgreSQL first.

---

## Validation Plan

1. **Unit tests:** Add test cases for each bug:
   - **Bug 1 (Idempotency):** Send a POST that returns 400, verify the response is NOT cached by sending the same request again with the same idempotency key and confirming it re-validates (or at minimum, verify a 400 response is not replayed as a cached response).
   - **Bug 5 (SLA):** Create a tracker with past response and completion deadlines, run `evaluate_trackers_and_escalate`, verify `health` remains `BREACHED_RESPONSE` (not downgraded to `BREACHED_COMPLETION`).
   - **Bug 6 (Fulfillment):** Create an APPROVED request, fulfill it to `FULFILLED`, then attempt to fulfill again — verify it raises 400.
   - **Bug 7 (Null check):** Simulate concurrent deletion between the initial fetch and re-query, verify a 404 is returned instead of 500.
   - **Bug 3 (Setup):** Mock `apiClient.post` to throw, verify `currentStep` does not advance.
   - **Bug 8 (DB engine):** Verify the default `db_engine` value in `SetupClient.tsx` is `'postgresql'`.

2. **Regression tests:** Run existing test suites:
   - `backend/tests/test_sla_engine.py`
   - `backend/tests/test_contractor_workforce.py`
   - `backend/tests/test_materials_inventory.py`
   - `backend/tests/test_idempotency.py`
   - `backend/tests/api/test_setup.py`
   - `backend/tests/test_backup_recovery.py`

3. **Frontend smoke test:** Verify Materials page (`/materials`) loads with only one catalog API call when the Catalog tab is active.

4. **E2E:** Run Playwright tests for setup wizard flow to confirm the DB engine default and step advancement behavior.
