# Tech Debt: Clean PR Branch Verification Gap

## Story

We created PR 918 as a clean, main-based replay of fixes that were already implemented and tested on `feat/ui-ux-revamp`. That improved reviewability, but it also introduced a verification debt: several commits had to be replayed with conflict resolution, and the resulting clean branch was not fully revalidated in its own environment.

The risk is not a known functional break. The risk is that a replayed or conflict-resolved file could differ slightly from the already-tested source branch, while the clean branch still looks correct in code review.

When we tried to remove that risk, the temporary worktree did not have a usable local test toolchain. CP and PP frontend reruns fell back to `npx`, which tried to fetch a newer `vitest` incompatible with the available Node 18 runtime. Mobile reruns similarly fell back to on-demand package resolution instead of using a ready local Jest toolchain. That means the branch is based on previously validated work, but the branch-specific final verification pass is still missing.

## Why This Matters

- PR 918 contains manual cherry-pick conflict resolution in CP, PP, and docs files.
- Review confidence is lower without a clean-branch verification pass.
- The current gap is environmental and process-related, not clearly product-related.

## Debt Item

**Name:** Clean branch test-environment parity for reviewer PRs

**Problem:** We can replay tested commits onto a clean branch faster than we can prove that the clean branch has the same executable state.

**Impact:** Reviewers may merge a branch that is logically correct but not independently revalidated after conflict resolution.

**Root cause:** The temporary PR worktree was missing ready-to-use local frontend and mobile test dependencies, and the fallback package install path was incompatible with the available Node runtime.

## What Is Needed To Pay This Debt Down

1. Install or reuse the correct local dependencies in the clean PR worktree for:
   - `src/CP/FrontEnd`
   - `src/PP/FrontEnd`
   - `src/mobile`
2. Re-run the targeted CP, PP, and mobile test suites on the clean PR branch itself.
3. Re-check the files that required conflict resolution during cherry-pick replay.
4. Treat clean-branch verification as part of PR packaging whenever replay or conflict resolution is involved.

## Approximate Dependency Cost

- CP frontend test toolchain: `250-400 MB`
- PP frontend test toolchain: `250-400 MB`
- Mobile Jest/Expo toolchain: `800 MB-1.5 GB`
- Optional Playwright browser binaries for browser smoke coverage: `600 MB-1 GB`

Practical mitigation size for this debt is roughly `1.3-2.3 GB` without Playwright, or higher if browser binaries are also installed.

## Recommended Follow-up

The next time we cut a clean PR from a larger branch, we should budget dependency setup as part of the PR-prep workflow, not as an afterthought. That converts this from a review-confidence risk into a routine packaging step.