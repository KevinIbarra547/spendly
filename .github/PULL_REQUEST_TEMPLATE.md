# Pull Request Template - Spendly

**⚠️ STOP: Before submitting this PR, ask Vibe Code to review it!**

---

## 📌 Description
[Clearly describe what this PR does. Reference the SPEC section or task number.]

**SPEC Reference:** [Link to SPEC section or "N/A - infrastructure"]
**Task:** [Link to GitHub issue or project task]

---

## ✅ Pre-Submission Checklist

**DO NOT SUBMIT until ALL of these are checked:**

- [ ] **SPEC Compliance:** I have read the relevant SPEC section and my changes match it **exactly**
- [ ] **Contract Match:** If this changes an API, it matches the contract in `src/shared/contracts/`
- [ ] **Tests Added:** I have added or updated tests for my changes
- [ ] **All Tests Pass:** `npm run test` passes locally
- [ ] **Linting Passes:** `npm run lint` passes locally
- [ ] **Type Checking Passes:** `npm run typecheck` passes locally
- [ ] **No Breaking Changes:** I have checked for breaking changes to existing features
- [ ] **Documentation Updated:** I have updated any relevant documentation
- [ ] **Feature Flags:** If this is a new feature, it's behind a feature flag set to `false`
- [ ] **Code Review:** I have asked Vibe Code to review this before submitting

---

## 🔗 Related Information

- **Depends On:** [List any PRs that must be merged first]
- **Blocks:** [List any PRs or tasks that depend on this]
- **Breaking Changes:** [Yes/No - If yes, describe what breaks and how to fix]

---

## 🧪 Testing

**How I tested my changes:**
- [ ] Unit tests pass (`npm run test:unit`)
- [ ] Integration tests pass (`npm run test:integration`)
- [ ] Reference model tests pass (`npm run test:reference`)
- [ ] Manual testing completed

**Test Results:**
```
[Paste test output here]
```

---

## 📊 Changes Summary

| File | Change Type | Risk Level | SPEC Section |
|------|-------------|------------|--------------|
| `src/backend/...` | [New/Modified/Deleted] | [Low/Medium/High] | [SPEC ref] |
| `src/frontend/...` | [New/Modified/Deleted] | [Low/Medium/High] | [SPEC ref] |
| `src/shared/...` | [New/Modified/Deleted] | [Low/Medium/High] | [SPEC ref] |

---

## 🚨 Known Issues
[List any known problems, limitations, or temporary workarounds]

---

## 👥 Required Reviewers

**Based on CODEOWNERS, this PR requires approval from:**
- [ ] @EthanGitHub (Backend changes)
- [ ] @KevinGitHub (Frontend changes)
- [ ] @CheyenneGitHub (Asset changes)
- [ ] @MylesGitHub (CI/Integration changes)

**Additional reviewers:**
@EthanGitHub @KevinGitHub @CheyenneGitHub @MylesGitHub

---

## 📝 Notes for Reviewers

[Any additional context or information that would help reviewers]

---

**✅ READY FOR REVIEW:** [Yes/No]

*If No, do not submit this PR. Fix the issues above first.*
