# DevReady Development Team Rules

**Version:** 1.0  
**Last Updated:** April 8, 2026  
**Maintainer:** Shuvam (unichronicles39)  
**Status:** Source of Truth for Development Team Compliance

---

## 🚨 Critical Git Rules

### 1. Branch Protection & Naming
- **NEVER push directly to `main` branch**
- Always create a feature branch for any changes
- **Each developer should have only ONE active branch at a time**
- Branch naming convention: `<github-username>/<type>-<description>`
  - Types: `feature`, `fix`, `docs`, `refactor`
  - Example: `shuvam/feature-scanner-engine`, `john/fix-memory-leak`, `alice/docs-api-reference`
- Delete your branch after it's merged before creating a new one
- If you need to work on multiple things, finish and merge one branch first

### 2. Force Push Policy
- **NEVER use `git push --force` or `git push -f`**
- If you encounter branch divergence, pull/push errors, or merge conflicts:
  - ⚠️ **STOP IMMEDIATELY**
  - ⚠️ **FLASH WARNING: "CALL SHUVAM!!"**
  - Do not attempt to resolve force push scenarios independently
  - Contact Shuvam before proceeding with any force operations

### 3. Pull Request Requirements
- All changes must go through PR review before merging
- PR title must clearly describe what you're building/fixing
- Link related issues in PR description
- At least 1 approval required before merge
- Ensure all CI/CD checks pass

---

## 📋 PRD Compliance Rules

### 4. Maintain PRD Alignment
- **All development work MUST comply with PRD.md**
- Before starting any feature:
  - Verify it's defined in PRD Section 5 (Key Features)
  - Confirm it's not in Section 8 (Out of Scope)
  - Understand the success metrics (Section 7)
  
### 5. Proposing Improvements or Changes
- If you think something can be done better or differently than the PRD:
  - ⚠️ **STOP and confirm with Shuvam before proceeding**
  - Document your proposal with clear rationale
  - Explain why it's better than the PRD approach
  - Wait for explicit approval - never assume it's okay to deviate
  - Update PRD.md if the change is approved

### 6. Performance Requirements
- All code must meet PRD Section 6 non-functional requirements:
  - Idle: < 2% CPU, < 150 MB RAM
  - Full scan: < 8 seconds
  - Measure and test performance before committing

---

## 💻 Code Quality Standards

### 7. Code Review Requirements
- Self-review your code before requesting review
- Address all review comments before merging
- Use meaningful commit messages (conventional commits format)
- Example: `feat: add dependency scanner`, `fix: resolve memory leak in watcher`

### 8. Testing Standards
- Write tests for all new features and bug fixes
- Run full test suite locally before pushing
- Don't merge if tests are failing
- Include both unit and integration tests where applicable

### 9. Code Style & Formatting
- Follow the project's linting rules (ESLint, Prettier, etc.)
- Run linter before committing: `npm run lint` or equivalent
- Keep functions small and focused
- Write self-documenting code with clear variable names

### 10. Documentation
- Update README.md for user-facing changes
- Add comments for complex logic
- Document all public APIs
- Keep CHANGELOG.md updated

---

## 🏗️ Development Workflow

### 11. Before Starting Work
1. Pull latest from `main`: `git pull origin main`
2. Check if you have an existing branch - delete it if already merged
3. Create your personal feature branch: `git checkout -b <your-github-username>/<type>-<description>`
   - Example: `git checkout -b shuvam/feature-drift-detection`
4. Check PRD.md to understand requirements
5. Break work into small, reviewable commits

### 12. During Development
- Commit frequently with clear messages
- Test your changes locally
- Keep your branch up to date with `main`
- Push your branch regularly: `git push origin your-branch`

### 13. Before Submitting PR
1. Run tests: `npm test` (or equivalent)
2. Run linter: `npm run lint`
3. Self-review your changes
4. Write clear PR description explaining what and why
5. Request review from team members

### 14. After PR Approval
- Squash commits if needed (discuss with team)
- Merge using GitHub/GitLab UI (never push to main directly)
- **Delete your feature branch immediately after merge**
- You can now create a new branch for your next task

---

## 🔒 Security & Best Practices

### 15. Sensitive Data
- Never commit API keys, tokens, or passwords
- Use `.env` files for secrets (and add to `.gitignore`)
- Never log sensitive user data
- Sanitize all user inputs

### 16. Dependency Management
- Review dependencies before adding them
- Keep dependencies updated regularly
- Use lock files (package-lock.json, Cargo.lock, etc.)
- Check for security vulnerabilities: `npm audit`

### 17. Error Handling
- Handle errors gracefully
- Provide helpful error messages
- Log errors with context for debugging
- Don't expose internal errors to end users

---

## 🤖 AI Coding Agent Standards

### 18. Using AI Coding Assistants
- Always review AI-generated code before committing
- Test AI code thoroughly - don't assume it works
- Ensure AI code follows team standards
- Add your own comments and context
- Take responsibility for all committed code (even if AI wrote it)

### 19. Agent Configuration
- Keep personal AI preferences out of shared configs
- Follow team's coding agent guidelines if they exist
- Don't commit `.cursor/`, `.copilot/` personal settings

---

## 📊 Performance & Quality

### 20. Performance Standards
- Profile code for bottlenecks before merging
- Ensure idle performance: < 2% CPU, < 150 MB RAM
- Keep scan times under 8 seconds
- Test on different machines/OS when possible

### 21. Cross-Platform Development
- Test on macOS, Windows, and Linux when possible
- Use platform-agnostic code where possible
- Handle OS-specific cases gracefully
- Document platform-specific behavior

---

## 📝 Communication

### 22. Team Communication
- Respond to PR reviews within 24-48 hours
- Ask questions if requirements are unclear
- Update issue/ticket status regularly
- Be respectful and constructive in code reviews

### 23. When Stuck
- Try to debug for 30 minutes first
- Search existing issues and documentation
- Ask team for help - don't stay blocked
- Document the solution for others

---

## ⚡ Quick Checklist

Before every commit:
- [ ] Code works and is tested locally
- [ ] Linter passes
- [ ] No sensitive data in code
- [ ] Meaningful commit message
- [ ] PRD compliance verified

Before every PR:
- [ ] Created branch from `main` (NOT pushing to `main`)
- [ ] Tests passing
- [ ] Self-reviewed changes
- [ ] Clear PR description
- [ ] Ready for review

When you see errors:
- [ ] Branch divergence? → **CALL SHUVAM!!**
- [ ] Force push needed? → **CALL SHUVAM!!**
- [ ] Want to deviate from PRD? → **Confirm with Shuvam first**

---

## 🆘 Emergency Contacts

- **Git Issues / Force Push Scenarios:** ⚠️ CALL SHUVAM!!
- **PRD Questions or Changes:** Contact Shuvam
- **Unclear Requirements:** Ask in team chat or contact Shuvam
- **Blocked on Something:** Don't stay stuck - reach out

---

## 🎯 Remember

These rules exist to:
- Keep the codebase clean and maintainable
- Ensure we're building what's in the PRD
- Prevent breaking changes and conflicts
- Maintain team consistency

**When in doubt, ask before proceeding. It's always better to clarify than to redo work.**

**This document is the source of truth for DevReady development team standards.**
