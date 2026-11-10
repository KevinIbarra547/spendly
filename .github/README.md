# GitHub Configuration - Spendly Project

This directory contains all GitHub-specific configuration files for the Spendly project.

## 📁 Files in this Directory

| File | Purpose | Status |
|------|---------|--------|
| `CODEOWNERS` | Defines who must review changes to specific code paths | ✅ Configured |
| `PULL_REQUEST_TEMPLATE.md` | Template for all pull requests | ✅ Configured |
| `ISSUE_TEMPLATE/` | Templates for GitHub issues | ✅ Configured |
| `workflows/ci.yml` | Continuous Integration pipeline | ✅ Configured |

## 🛡️ Protection Rules Implemented

### 1. CODEOWNERS
**Status:** ✅ File created, needs GitHub usernames

This file ensures that:
- Backend changes require **@EthanGitHub** approval
- Frontend changes require **@KevinGitHub** approval
- Asset changes require **@CheyenneGitHub** approval
- CI/Integration changes require **@MylesGitHub** approval

**Action Required:** Replace placeholder usernames with actual GitHub usernames!

### 2. Pull Request Template
**Status:** ✅ Configured

This template ensures that every PR includes:
- Clear description and SPEC reference
- Pre-submission checklist (SPEC compliance, tests, linting, etc.)
- Related information (dependencies, blocks, etc.)
- Testing summary
- Changes summary table
- Known issues
- Required reviewers

**Effect:** Prevents incomplete or poorly documented PRs from being submitted.

### 3. Issue Templates
**Status:** ✅ Configured

Two templates are available:
- **Feature Request** - For new features or improvements
- **Bug Report** - For reporting bugs

Both templates ensure:
- Clear descriptions
- Acceptance criteria (for features)
- Reproduction steps (for bugs)
- SPEC references
- Ownership assignment
- Priority and effort estimation

**Effect:** Ensures all issues have the information needed to be worked on.

### 4. CI/CD Pipeline
**Status:** ✅ Workflow file created

The CI pipeline (`ci.yml`) runs on every push and pull request and includes:

| Job | Purpose | When Runs |
|-----|---------|-----------|
| `lint` | ESLint + TypeScript type checking | Always |
| `test-unit` | Unit tests | After lint passes |
| `test-integration` | Integration tests with PostgreSQL | After unit tests |
| `test-reference` | Reference model comparison | After unit tests |
| `build` | Project build verification | After all tests |
| `validate-contracts` | API contract validation | After lint |
| `test-regression` | Regression tests | After unit tests |

**Effect:** Blocks any PR that:
- Fails linting
- Fails type checking
- Fails any tests
- Breaks the build
- Doesn't match API contracts
- Breaks existing functionality

## ⚙️ Branch Protection (MANUAL SETUP REQUIRED)

**Status:** ❌ NOT YET CONFIGURED

You **MUST** manually configure branch protection in GitHub:

### For `main` branch:
1. Go to **Settings > Branches > Branch protection rules**
2. Click **Add rule**
3. Set **Branch name pattern:** `main`
4. Enable these options:
   - [x] **Require a pull request before merging**
     - [x] Require approvals: **2**
     - [x] Require review from Code Owners
     - [x] Dismiss stale pull request approvals when new commits are pushed
   - [x] **Require status checks to pass before merging**
     - [x] Require branches to be up to date before merging
     - [x] Status checks that are required:
       - `ci/lint`
       - `ci/test-unit`
       - `ci/test-integration`
       - `ci/test-reference`
       - `ci/build`
   - [x] **Include administrators**
   - [x] **Restrict who can push to matching branches**
     - Only allow specific people: **NONE** (block all direct pushes)
   - [x] **Do not allow bypassing the above settings**

### For `dev` branch:
1. Same as `main`, but with:
   - Require approvals: **1**
   - Can allow some direct pushes if needed

## 🎯 Feature Flags

**Status:** ⏳ To be implemented

Feature flags will be added in Phase 0 to prevent unfinished features from being used.

## 📊 Protection Summary

| Protection Type | Status | Effect |
|----------------|--------|--------|
| Branch Protection | ❌ Manual setup needed | Prevents direct pushes to main |
| CODEOWNERS | ✅ File created | Requires specific reviewers |
| PR Template | ✅ Configured | Ensures proper documentation |
| Issue Templates | ✅ Configured | Ensures clear requirements |
| CI Pipeline | ✅ Configured | Blocks breaking changes |
| Pre-commit Hooks | ⏳ Needs setup | Local quality gates |
| Feature Flags | ⏳ Needs implementation | Prevents using unfinished features |

## 🚀 Next Steps

1. **✅ DONE:** Protection files created
2. **⏳ TODO:** Replace placeholder usernames in CODEOWNERS
3. **⏳ TODO:** Configure branch protection in GitHub settings
4. **⏳ TODO:** Run `scripts/setup.sh` to initialize the project
5. **⏳ TODO:** Start Phase 0: Foundation

## 💡 Important Notes

- **CODEOWNERS only works if usernames are correct** - Replace `@EthanGitHub`, `@KevinGitHub`, etc. with actual GitHub usernames
- **Branch protection must be configured manually** - GitHub doesn't allow API configuration without admin access
- **CI pipeline will fail until tests are implemented** - This is expected. Add tests as you build features
- **Pre-commit hooks need husky** - Run `npm run prepare` after installing dependencies

## 📚 Resources

- [GitHub CODEOWNERS Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-code-and-commits/using-codeowners-to-manage-code-ownership-and-permissions)
- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
