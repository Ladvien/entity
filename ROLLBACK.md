# Emergency Rollback Procedure

**Document Version:** 1.0
**Last Updated:** Q2 2024
**Applies To:** Entity Framework v0.1.0 Modularization Release

---

## 🚨 When to Execute Rollback

Execute this rollback procedure if any of the following critical issues occur within 48 hours of the v0.1.0 release:

### Critical Issues
- **Import failures** affecting >10% of users
- **Data corruption** or **memory leaks** in the compatibility layer
- **Performance regressions** >50% worse than v0.0.12
- **Security vulnerabilities** in the new modular structure
- **Dependency conflicts** preventing installation

### Non-Critical Issues (Do NOT rollback)
- Individual user configuration issues
- Minor deprecation warning confusion
- Single plugin compatibility issues
- Documentation gaps or typos

---

## ⏱️ Rollback Timeline

| Time After Release | Action Required | Responsibility |
|-------------------|----------------|----------------|
| 0-2 hours | Monitor deployment metrics | DevOps Team |
| 2-8 hours | Assess user reports | Support Team |
| 8-24 hours | Decision point for rollback | Technical Lead |
| 24-48 hours | Final rollback window | Release Manager |
| 48+ hours | Post-mortem, hotfix only | Engineering Team |

---

## 🛡️ Pre-Rollback Checklist

Before executing rollback, verify:

- [ ] **Critical issue confirmed** (not user error or configuration)
- [ ] **Scope assessment** completed (affects >5% of users)
- [ ] **Hotfix attempts** failed or deemed too risky
- [ ] **Stakeholder approval** obtained (Technical Lead + Product Owner)
- [ ] **Communication plan** ready for users
- [ ] **Rollback team** assembled and ready

---

## 🔄 Rollback Procedures

### Option 1: Git-Based Rollback (Recommended)

```bash
# 1. Checkout the pre-modularization state
git checkout pre-modularization

# 2. Create rollback branch
git checkout -b rollback-v0.1.0-emergency
git tag v0.0.13-rollback

# 3. Update version in pyproject.toml
sed -i 's/version = "0.1.0"/version = "0.0.13"/' pyproject.toml

# 4. Restore the original GPT-OSS plugins
git checkout pre-modularization -- src/entity/plugins/gpt_oss/

# 5. Remove compatibility layer
rm src/entity/plugins/gpt_oss_compat.py

# 6. Update __init__.py files to original state
git checkout pre-modularization -- src/entity/plugins/gpt_oss/__init__.py

# 7. Commit rollback changes
git add -A
git commit -m "EMERGENCY ROLLBACK: Restore v0.0.12 functionality

- Restore original GPT-OSS plugins in main package
- Remove compatibility layer causing issues
- Revert to stable import patterns
- Version bumped to 0.0.13 for clarity

Critical issue: [ISSUE-ID]
Rollback approved by: [APPROVER-NAME]"

# 8. Push to main (requires force push)
git push origin rollback-v0.1.0-emergency:main --force-with-lease
```

### Option 2: Package-Based Rollback

```bash
# 1. Revert PyPI package to working state
# Upload 0.0.13 with restored functionality

# 2. Build rollback package
poetry version 0.0.13
poetry build

# 3. Upload to PyPI
poetry publish

# 4. Update documentation
echo "ROLLBACK NOTICE: v0.1.0 has been rolled back due to critical issues." >> README.md
```

### Option 3: Hotfix Release (If rollback not feasible)

```bash
# 1. Create hotfix branch
git checkout -b hotfix-v0.1.1

# 2. Apply minimal fixes only
# [Apply specific fixes here]

# 3. Version bump to 0.1.1
poetry version 0.1.1

# 4. Emergency release
poetry build && poetry publish
```

---

## 📦 Package Restoration

### PyPI Package Management

```bash
# Verify rollback packages are available
pip install entity-core==0.0.13

# If needed, restore from backup
aws s3 cp s3://entity-releases-backup/v0.0.12/ ./packages/ --recursive

# Re-upload to PyPI
twine upload packages/*
```

### Docker Image Rollback

```bash
# Tag latest stable image
docker tag entity-core:v0.0.12 entity-core:latest

# Push updated latest tag
docker push entity-core:latest

# Update Docker Hub description with rollback notice
```

---

## 📢 Communication Plan

### Immediate Notification (Within 1 hour)

```markdown
🚨 URGENT: Entity Framework v0.1.0 Rollback Notice

We've identified critical issues with v0.1.0 and are rolling back to v0.0.12.

IMMEDIATE ACTION REQUIRED:
- Do NOT upgrade to v0.1.0 until further notice
- If already upgraded, downgrade: pip install entity-core==0.0.12
- Monitor our status page for updates

We apologize for the inconvenience and are working to resolve this quickly.

Status: https://status.entity-framework.com
Updates: Follow @EntityFramework
```

### User Communication Channels

1. **GitHub Release Notes** - Prominent warning banner
2. **PyPI Package Description** - Rollback notice
3. **Documentation Site** - Alert banner on all pages
4. **Social Media** - Twitter, LinkedIn announcements
5. **Email List** - Direct notification to subscribers
6. **Discord/Slack** - Community announcements

### Stakeholder Communication

```
Subject: URGENT - Entity Framework v0.1.0 Emergency Rollback

Stakeholders,

Entity Framework v0.1.0 has been rolled back due to critical issues:
- Issue Type: [DESCRIBE CRITICAL ISSUE]
- User Impact: [SCOPE OF IMPACT]
- Timeline: Rollback completed at [TIMESTAMP]

Actions Taken:
- Immediate rollback to v0.0.12 functionality
- PyPI packages updated with working versions
- User communication deployed across all channels

Next Steps:
- Root cause analysis in progress
- Fix timeline: [ESTIMATED TIME]
- Post-mortem scheduled for [DATE]

We will provide updates every 4 hours until resolved.

[NAME]
Release Manager
```

---

## 🧪 Post-Rollback Verification

### Automated Checks

```bash
# 1. Verify rollback package functionality
pip install entity-core==0.0.13
python -c "
import entity
from entity.plugins.gpt_oss import ReasoningTracePlugin
print('✅ Rollback verification successful')
"

# 2. Run critical test suite
pytest tests/test_critical_functionality.py -v

# 3. Performance regression test
python benchmarks/pre_modularization_benchmark.py

# 4. Import time verification
python -c "
import time
start = time.time()
import entity.plugins.gpt_oss
end = time.time()
print(f'Import time: {end-start:.4f}s')
assert (end-start) < 0.5, 'Import too slow'
print('✅ Performance verification successful')
"
```

### Manual Verification Checklist

- [ ] **Core functionality** works (Agent creation, basic plugins)
- [ ] **GPT-OSS plugins** import without warnings
- [ ] **Example applications** run successfully
- [ ] **Documentation** reflects correct version
- [ ] **PyPI package** shows correct version and description
- [ ] **No compatibility warnings** in logs

---

## 🔍 Root Cause Analysis

### Required Investigation

Within 24 hours of rollback completion:

1. **Technical Analysis**
   - Identify the root cause of critical issues
   - Document what went wrong in the modularization
   - Review testing gaps that missed the issues

2. **Process Analysis**
   - Review release process for improvement opportunities
   - Assess testing coverage and quality gates
   - Identify early warning signs that were missed

3. **Communication Analysis**
   - Review user feedback and response time
   - Assess effectiveness of rollback communication
   - Document lessons learned for future releases

### Post-Mortem Template

```markdown
## Post-Mortem: v0.1.0 Emergency Rollback

### Timeline
- [TIMESTAMP] Release deployed
- [TIMESTAMP] First issue reports
- [TIMESTAMP] Critical issue confirmed
- [TIMESTAMP] Rollback decision made
- [TIMESTAMP] Rollback completed

### Root Cause
[Detailed technical explanation]

### Contributing Factors
- [Factor 1]
- [Factor 2]

### Impact Assessment
- Users affected: [NUMBER]
- Downtime duration: [TIME]
- Support tickets: [NUMBER]

### What Went Well
- [Positive aspect 1]
- [Positive aspect 2]

### What Went Wrong
- [Issue 1]
- [Issue 2]

### Action Items
- [ ] [Action item 1] - Owner: [NAME] - Due: [DATE]
- [ ] [Action item 2] - Owner: [NAME] - Due: [DATE]

### Prevention Measures
- [Preventive measure 1]
- [Preventive measure 2]
```

---

## 🚀 Recovery Plan

### Path Forward After Rollback

1. **Immediate (0-7 days)**
   - Complete root cause analysis
   - Fix critical issues identified
   - Enhanced testing for problem areas

2. **Short-term (1-4 weeks)**
   - Implement additional safeguards
   - Beta release with limited users
   - Extended testing period

3. **Long-term (1-3 months)**
   - Re-release modularization with fixes
   - Improved deployment process
   - Enhanced monitoring and alerting

### Re-Release Criteria

Before attempting v0.1.1 or v0.2.0:

- [ ] **Root cause fixed** and verified
- [ ] **Enhanced test coverage** for problem areas
- [ ] **Beta testing** with real users completed
- [ ] **Performance benchmarks** meet or exceed v0.0.12
- [ ] **Rollback procedures** tested and refined
- [ ] **Monitoring alerts** configured for early detection

---

## 👨‍💻 Emergency Contacts

### Rollback Authority Chain

1. **Technical Lead:** [NAME] - [PHONE] - [EMAIL]
2. **Release Manager:** [NAME] - [PHONE] - [EMAIL]
3. **DevOps Lead:** [NAME] - [PHONE] - [EMAIL]
4. **Product Owner:** [NAME] - [PHONE] - [EMAIL]

### Execution Team

- **Git Operations:** DevOps Team
- **PyPI Management:** Release Manager
- **Communication:** Product Team
- **Testing/Verification:** QA Team
- **Support:** Customer Success Team

---

## 📋 Rollback Checklist

Print and keep handy during release:

### Pre-Rollback (Decision Phase)
- [ ] Critical issue confirmed and documented
- [ ] Impact assessment completed (affects >5% users)
- [ ] Hotfix deemed not feasible or too risky
- [ ] Stakeholder approval obtained
- [ ] Communication plan prepared
- [ ] Rollback team assembled

### During Rollback (Execution Phase)
- [ ] Git rollback branch created
- [ ] Code reverted to stable state
- [ ] Version numbers updated appropriately
- [ ] PyPI packages uploaded
- [ ] Docker images updated
- [ ] Documentation updated with rollback notices

### Post-Rollback (Verification Phase)
- [ ] Automated tests pass
- [ ] Manual verification completed
- [ ] User communication sent
- [ ] Monitoring confirms stable state
- [ ] Support team briefed
- [ ] Post-mortem scheduled

### Recovery Phase
- [ ] Root cause analysis completed
- [ ] Fix implementation plan created
- [ ] Enhanced testing plan developed
- [ ] Re-release criteria defined
- [ ] Process improvements documented

---

**Remember: Rollback is a safety mechanism, not a failure. Quick decisive action to protect users is always the right choice when facing critical issues.**
