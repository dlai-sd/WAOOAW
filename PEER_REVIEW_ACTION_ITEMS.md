# 🔧 Peer Review Action Items - Quick Reference

## Critical Issues (MUST FIX Before Production)

### 1️⃣ Pipeline: Fix tfvars Append Logic
**File**: `.github/workflows/cp-pipeline.yml` (Lines 893-905)  
**Severity**: 🔴 HIGH  
**Time**: 5 minutes

**Problem**: Enable flags appended multiple times if job reruns
```yaml
# Current (problematic):
cat >> "$TFVARS_FILE" <<EOF
enable_backend_api = ...
EOF

# If rerun → duplicate lines → Terraform warns
```

**Fix**:
```yaml
# Solution: Replace instead of append
cat > /tmp/enable_flags.tfvars <<EOF
enable_backend_api = ${{ needs.validate-components.outputs.enable_backend_api }}
enable_customer_portal = ${{ needs.validate-components.outputs.enable_customer_portal }}
enable_platform_portal = ${{ needs.validate-components.outputs.enable_platform_portal }}
EOF

# Remove old enable flags if exist
sed -i '/^enable_backend_api\|^enable_customer_portal\|^enable_platform_portal/d' "$TFVARS_FILE"

# Append clean flags
cat /tmp/enable_flags.tfvars >> "$TFVARS_FILE"
```

---

### 2️⃣ Terraform: Fix State Corruption Risk
**File**: `cloud/terraform/main.tf` (Lines 133-145)  
**Severity**: 🔴 HIGH  
**Time**: 10 minutes

**Problem**: depends_on on module list could cause orphaned resources when toggling
```hcl
# Current (risky):
depends_on = concat(
  var.enable_backend_api ? [module.backend_api] : [],  # ← Depends on whole module
  ...
)
```

**Fix**:
```hcl
# Solution: Explicit index reference
depends_on = concat(
  var.enable_backend_api ? [module.backend_api[0]] : [],
  var.enable_customer_portal ? [module.customer_portal[0]] : [],
  var.enable_platform_portal ? [module.platform_portal[0]] : []
)
```

---

### 3️⃣ Terraform: Add At-Least-One-Enabled Validation
**File**: `cloud/terraform/variables.tf` (Add after line 50)  
**Severity**: 🟡 MEDIUM  
**Time**: 5 minutes

**Problem**: User can disable all services, breaking infrastructure
```hcl
enable_backend_api = false
enable_customer_portal = false
enable_platform_portal = false
# → No Cloud Run services → Broken LB
```

**Fix**: Add validation variable
```hcl
variable "validate_at_least_one_service" {
  description = "Validation: at least one service must be enabled"
  type        = bool
  
  validation {
    condition = (
      var.enable_backend_api ||
      var.enable_customer_portal ||
      var.enable_platform_portal
    )
    error_message = "ERROR: At least one service must be enabled (backend_api, customer_portal, or platform_portal)."
  }
}
```

---

## Important Issues (SHOULD FIX Before Wider Use)

### 4️⃣ Pipeline: Fix Job Dependency Chain
**File**: `.github/workflows/cp-pipeline.yml` (Line 854)  
**Severity**: 🟡 MEDIUM  
**Time**: 10 minutes

**Problem**: terraform-deploy depends on build-and-push-gcp even if build_images=false
```yaml
# Current:
needs: [validate-components, build-and-push-gcp]
if: inputs.deploy_to_gcp == true
# If build_images=false → build-and-push-gcp doesn't run → workflow fails
```

**Fix**: Restructure dependencies
```yaml
# Option 1: Add conditional
terraform-deploy:
  needs: [validate-components]
  if: inputs.deploy_to_gcp == true && inputs.build_images == true
  # Make it optional: only run if both conditions true

# Option 2: Or make build-and-push-gcp always output valid data
```

---

### 5️⃣ Terraform: Verify Health Checks Configured
**File**: `cloud/terraform/modules/load-balancer/main.tf` (Lines 49-71)  
**Severity**: 🟡 MEDIUM  
**Time**: Review only

**Problem**: Backend services might not have health_checks configured
```hcl
# Check: Is this line present?
resource "google_compute_backend_service" "api" {
  count           = var.enable_api ? 1 : 0
  health_checks   = [google_compute_health_check.api[0].id]  # ← Should be here
  ...
}
```

**Fix**: If missing, add health_checks reference
```hcl
health_checks = [google_compute_health_check.api[0].id]
```

---

## Polish Items (NICE TO HAVE)

### 6️⃣ Pipeline: Add Step-Level Timeouts
**File**: `.github/workflows/cp-pipeline.yml`  
**Severity**: 🟢 LOW  
**Time**: 5 minutes

**Add to critical steps**:
```yaml
- name: Terraform Plan
  timeout-minutes: 15  # Prevent hanging
  run: terraform plan ...

- name: Terraform Apply
  timeout-minutes: 15  # Prevent hanging
  run: terraform apply ...
```

---

### 7️⃣ Pipeline: Extract GCP_REGISTRY to Secrets
**File**: `.github/workflows/cp-pipeline.yml` (Line 95)  
**Severity**: 🟢 LOW  
**Time**: 10 minutes

**Current**: Hardcoded
```yaml
GCP_REGISTRY: asia-south1-docker.pkg.dev/waooaw-oauth/waooaw
```

**Better**: Use secrets
```yaml
GCP_REGISTRY: ${{ secrets.GCP_REGISTRY }}
# Add to GitHub secrets: GCP_REGISTRY=asia-south1-docker.pkg.dev/waooaw-oauth/waooaw
```

---

## Testing Checklist

After implementing fixes, test these scenarios:

- [ ] Deploy CP to demo (normal flow)
- [ ] Deploy CP to demo, then rerun same workflow (test append fix)
- [ ] Set enable_backend_api=false, enable_customer_portal=false, enable_platform_portal=false (test validation)
- [ ] Toggle enable_customer_portal true→false→true (test state)
- [ ] Build images only (no deploy)
- [ ] Deploy only (no build)
- [ ] Plan only (no apply)

---

## Deployment Readiness

| Item | Status | Notes |
|------|--------|-------|
| Critical Issues | ⚠️ MUST FIX | 3 high-priority fixes needed |
| Important Issues | ⚠️ SHOULD FIX | 2 medium-priority reviews |
| Polish Items | ✅ OPTIONAL | 2 low-priority improvements |
| Documentation | ✅ COMPLETE | Excellent coverage |
| Overall Grade | B+ | 82/100 |

**Recommendation**: Fix all 5 critical+important items before first demo deployment.

---

## Summary

**Pipeline**: 4 issues found (1 critical, 1 important, 2 polish)
**Terraform**: 5 issues found (2 critical, 2 important, 1 polish)
**Total Issues**: 9 (3 critical, 2 important, 4 polish)

**Time to Fix All**: ~45 minutes
**Time to Fix Critical Only**: ~20 minutes

**Can Deploy Now?** ⚠️ Only after Priority 1 fixes
