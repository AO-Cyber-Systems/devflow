# PRD-006: SDLC Tool Integrations

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Overview

DevFlow integrates bidirectionally with industry-standard SDLC tools to provide a unified development workflow. This PRD defines how DevFlow synchronizes with Atlassian tools (Jira, Confluence, Bitbucket) and GitHub while maintaining DevFlow as the authoritative source of truth for type hierarchy enforcement.

---

## Goals

### Primary Goals
1. **Bidirectional Synchronization**: Changes flow seamlessly between DevFlow and external systems
2. **Type Hierarchy Enforcement**: DevFlow strictly enforces PRD → Epic → Story → Task → Subtask structure
3. **User-Level OAuth**: Individual user authentication for secure, personalized access
4. **Atlassian-First Priority**: Prioritize Atlassian integrations, then GitHub
5. **Single Source of Truth**: DevFlow maintains authoritative type relationships

### Secondary Goals
1. Enable teams to use their existing SDLC tools without disruption
2. Provide conflict resolution UI for sync issues
3. Support automatic custom field creation in external systems
4. Maintain comprehensive sync audit trail
5. Enable selective sync (choose which projects/spaces to integrate)

---

## Integration Principles

### Core Principles

**1. DevFlow as Source of Truth**
- DevFlow owns the type hierarchy
- External systems cannot create invalid parent-child relationships
- Violations are **rejected** with user notification

**2. Atlassian Priority**
- Jira is the primary issue tracking integration
- Confluence is the primary documentation integration
- Bitbucket integration for code repositories
- GitHub as secondary alternative/supplement

**3. User-Level OAuth**
- Each user authenticates individually
- Tokens stored encrypted per user
- API calls made on behalf of authenticated user
- Respects user permissions in external systems

**4. Bidirectional Sync**
- Changes propagate in both directions
- Conflict resolution via dashboard review
- Last-modified timestamp determines winning change
- Manual override available for conflicts

**5. Non-Invasive Integration**
- Use existing spaces/projects where possible
- Create new spaces only when needed
- Use custom fields and properties (not core fields)
- Maintain compatibility with existing workflows

---

## Type Hierarchy Mapping

### DevFlow Canonical Type Hierarchy

```
PRD (Product Requirements Document)
├── Epic
│   ├── Story
│   │   ├── Task
│   │   │   └── Subtask
```

**Hierarchy Rules (STRICTLY ENFORCED):**
- PRD is the root level (optional, but recommended)
- Epic can exist under PRD or standalone
- Story MUST have Epic parent
- Task MUST have Story parent
- Subtask MUST have Task parent
- No skipping levels allowed

### Mapping to Atlassian

#### Jira Issue Type Mapping

| DevFlow Type | Jira Issue Type | Parent Field | Notes |
|--------------|-----------------|--------------|-------|
| **PRD** | Epic | N/A (root) | Special epic with custom field `DevFlow PRD ID` |
| **Epic** | Epic | Epic Link → PRD Epic | Links to parent PRD if exists |
| **Story** | Story | Epic Link → Epic | Standard Jira Story |
| **Task** | Task | Parent → Story | Uses parent link or issue link |
| **Subtask** | Sub-task | Parent → Task | Standard Jira Sub-task |

**Jira Custom Fields (Created by DevFlow):**
```
- DevFlow PRD ID (text)
- DevFlow Epic ID (text)
- DevFlow Story ID (text)
- DevFlow Task ID (text)
- DevFlow Subtask ID (text)
- DevFlow Sync Status (select: synced, conflict, pending, error)
- DevFlow Last Sync (datetime)
- Confluence Page ID (text) - for PRDs/Epics
- GitHub Issue Number (number)
- GitHub PR Number (number)
```

**Jira Issue Properties (Hidden Metadata):**
```json
{
  "devflow": {
    "type": "story",
    "id": "story-uuid-here",
    "parentId": "epic-uuid-here",
    "syncedAt": "2025-11-18T14:30:00Z",
    "conflictStatus": null,
    "metadata": {
      "confluencePageId": "123456",
      "githubIssueNumber": 42
    }
  }
}
```

#### Confluence Mapping

| DevFlow Type | Confluence Structure | Template |
|--------------|----------------------|----------|
| **PRD** | Page in designated space | PRD Template (customizable) |
| **Epic** | Child page under PRD | Epic Template |
| **Story** | Child page under Epic (optional) | Story Template |
| **Task** | Referenced in Story page (optional) | N/A |
| **Subtask** | Checklist in Task (optional) | N/A |

**Confluence Content Properties:**
```json
{
  "devflow": {
    "type": "prd",
    "id": "prd-uuid-here",
    "jiraEpicKey": "PROJ-100",
    "githubMilestone": 5,
    "syncedAt": "2025-11-18T14:30:00Z"
  }
}
```

**Confluence Space Strategy:**
- Option 1: Use existing space (user selects during setup)
- Option 2: Create new space "DevFlow - [Project Name]"
- Pages organized by PRD → Epic → Story hierarchy
- Use page tree to mirror DevFlow hierarchy

### Mapping to GitHub & DevFlow Code

DevFlow treats GitHub and **DevFlow Code** (PRD-010) as interchangeable Git providers.

| DevFlow Type | Git Entity | Notes |
|--------------|------------|-------|
| **PRD** | Milestone | Links to documentation |
| **Epic** | Project | Kanban board for tracking |
| **Story** | Issue | `story` label |
| **Task** | Issue | `task` label, linked to Story |
| **Code** | Repository | Synced to DevFlow Code |

**DevFlow Code Mirroring**:
- GitHub repositories can be mirrored to DevFlow Code
- PRs in GitHub sync to DevFlow Code PRs
- AI Code Review results post back to GitHub PRs
```
devflow-prd       (color: #7B68EE)
devflow-epic      (color: #FF6B6B)
devflow-story     (color: #4ECDC4)
devflow-task      (color: #95E77D)
devflow-subtask   (color: #FFE66D)
devflow-synced    (color: #6BCF7F)
devflow-conflict  (color: #FF6B6B)
```

**GitHub Issue Body Template:**
```markdown
<!-- DevFlow Sync Metadata -->
<!-- devflow-id: story-uuid-here -->
<!-- devflow-type: story -->
<!-- devflow-parent: epic-uuid-here -->
<!-- devflow-synced: 2025-11-18T14:30:00Z -->

[Original issue content]

---
**🔗 Related Links**
- Jira: [PROJ-123](https://jira.example.com/browse/PROJ-123)
- Confluence: [Epic Documentation](https://confluence.example.com/...)
- DevFlow: [View in DevFlow](https://devflow.example.com/story/uuid)
```

**GitHub Projects (Beta) Integration:**
- Create Project for each Epic
- Columns: Backlog, Ready, In Progress, Review, Done
- Auto-sync with Jira workflow states
- Use Project custom fields for DevFlow IDs

---

## OAuth & Authentication

### Token Storage Strategy

DevFlow prioritizes security for sensitive OAuth tokens using a tiered approach (see **PRD-007: Secrets Management**).

**1. 1Password Connect (Recommended)**
- Tokens stored in 1Password Vault
- Accessed via Connect Server API
- Audit logs provided by 1Password
- Best for Enterprise/Production

**2. Encrypted Database (Fallback)**
- Tokens stored in PostgreSQL `user_integrations` table
- AES-256-GCM encryption
- Key management via environment variables
- Suitable for Local/SaaS MVP

### Atlassian OAuth 2.0 (3LO)

**OAuth Flow:**
```
┌─────────────────────────────────────────────────────────────┐
│ 1. User clicks "Connect Atlassian" in DevFlow Settings     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. DevFlow redirects to Atlassian OAuth consent screen     │
│    URL: https://auth.atlassian.com/authorize               │
│    Params:                                                  │
│    - client_id: {DevFlow App ID}                           │
│    - redirect_uri: https://devflow.example.com/oauth/callback│
│    - scope: read:jira-work write:jira-work ...            │
│    - response_type: code                                    │
│    - state: {CSRF token}                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 3. User reviews permissions and clicks "Allow"              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. Atlassian redirects back to DevFlow with auth code      │
│    URL: https://devflow.example.com/oauth/callback?code=... │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 5. DevFlow exchanges code for access/refresh tokens        │
│    POST https://auth.atlassian.com/oauth/token             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 6. DevFlow stores encrypted tokens in database             │
│    - access_token (expires in 1 hour)                      │
│    - refresh_token (expires in 90 days)                    │
│    - cloud_id (Atlassian site identifier)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 7. DevFlow makes API calls on behalf of user               │
│    Header: Authorization: Bearer {access_token}            │
└─────────────────────────────────────────────────────────────┘
```

**Required Atlassian Scopes:**

```
OAuth 2.0 Scopes:
- read:jira-work               (Read issues, projects, boards)
- write:jira-work              (Create/update issues)
- read:jira-user               (Get user information)
- write:jira-user              (Update user properties)
- read:confluence-content.all  (Read all Confluence content)
- write:confluence-content     (Create/update pages)
- read:confluence-space.summary (List spaces)
- write:confluence-space       (Create spaces)
- read:confluence-props        (Read content properties)
- write:confluence-props       (Write content properties)
- offline_access               (Refresh tokens)
```

**Atlassian Cloud ID Discovery:**

```
1. After OAuth, call:
   GET https://api.atlassian.com/oauth/token/accessible-resources
   
2. Response:
   [
     {
       "id": "35273b54-3f06-40d2-880f-dd28cf8daafa",
       "name": "My Company Jira",
       "url": "https://mycompany.atlassian.net",
       "scopes": ["read:jira-work", "write:jira-work"],
       "avatarUrl": "https://..."
     }
   ]
   
3. User selects which site to integrate (if multiple)
4. Store cloud_id for API calls
```

**API Base URLs with Cloud ID:**

```
Jira REST API:
https://api.atlassian.com/ex/jira/{cloudId}/rest/api/3/{resource}

Confluence REST API:
https://api.atlassian.com/ex/confluence/{cloudId}/rest/api/{resource}
```

### GitHub OAuth

**OAuth Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User clicks "Connect GitHub" in DevFlow Settings        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. DevFlow redirects to GitHub OAuth screen                │
│    URL: https://github.com/login/oauth/authorize           │
│    Params:                                                  │
│    - client_id: {DevFlow GitHub App ID}                    │
│    - redirect_uri: https://devflow.example.com/oauth/github │
│    - scope: repo read:org write:discussion read:project    │
│    - state: {CSRF token}                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 3. User authorizes DevFlow                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. GitHub redirects with code                               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 5. DevFlow exchanges code for access token                 │
│    POST https://github.com/login/oauth/access_token        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 6. Store encrypted token (GitHub tokens don't expire)      │
└─────────────────────────────────────────────────────────────┘
```

**Required GitHub Scopes:**

```
OAuth Scopes:
- repo                  (Full repository access)
- read:org              (Read organization data)
- write:discussion      (Create/update discussions)
- read:project          (Read project boards)
- write:project         (Manage project boards)
- read:user             (Read user profile)
```

### Token Storage Schema

```sql
CREATE TABLE user_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL, -- 'atlassian' or 'github'
    
    -- Encrypted OAuth tokens
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    
    -- Platform-specific identifiers
    cloud_id TEXT,              -- Atlassian cloud ID
    site_url TEXT NOT NULL,     -- Full site URL
    site_name TEXT,             -- Display name
    
    -- User info from platform
    platform_user_id TEXT,      -- User ID on external platform
    platform_username TEXT,     -- Username on external platform
    platform_email TEXT,        -- Email on external platform
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, expired, revoked, error
    last_sync_at TIMESTAMPTZ,
    
    -- Metadata
    scopes TEXT[],              -- Granted OAuth scopes
    metadata JSONB,             -- Additional platform-specific data
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, platform, cloud_id)
);

CREATE INDEX idx_user_integrations_user ON user_integrations(user_id);
CREATE INDEX idx_user_integrations_status ON user_integrations(status);
CREATE INDEX idx_user_integrations_expires ON user_integrations(token_expires_at);
```

**Token Encryption:**
- Use AES-256-GCM encryption
- Unique key per environment (stored in secure vault)
- Rotate encryption keys quarterly
- Never log decrypted tokens

**Token Refresh Strategy:**
- Check expiration before each API call
- Auto-refresh if expires within 5 minutes
- Update database with new tokens
- Retry failed API calls after refresh

---

## Webhook Architecture

### Deployment Modes

**1. SaaS / Hosted (Production)**
- Direct HTTPS endpoints
- `https://api.devflow.dev/webhooks/jira`
- Secured by TLS and signature verification

**2. Local Development (Dev)**
- Webhook Proxy (e.g., smee.io or ngrok) required
- DevFlow CLI automatically starts proxy tunnel
- `smee -u https://smee.io/devflow-local -t http://localhost:8000/webhooks/jira`

### Sync Mechanisms

**1. Webhooks (Primary - Real-time)**
```
Webhook URL: https://devflow.example.com/api/webhooks/jira
Events:
- jira:issue_created
- jira:issue_updated
- jira:issue_deleted
- jira:issue_link_created
- jira:issue_link_deleted

Webhook Payload:
{
  "webhookEvent": "jira:issue_updated",
  "issue": {
    "key": "PROJ-123",
    "fields": {
      "issuetype": {"name": "Story"},
      "summary": "Updated title",
      "parent": {"key": "PROJ-100"},
      ...
    }
  }
}
```

**Confluence Webhooks:**
```
Webhook URL: https://devflow.example.com/api/webhooks/confluence
Events:
- page_created
- page_updated
- page_removed
- page_trashed

Webhook Payload:
{
  "event": "page_updated",
  "page": {
    "id": "123456",
    "title": "PRD: Mobile App",
    "version": {"number": 5},
    ...
  }
}
```

**GitHub Webhooks:**
```
Webhook URL: https://devflow.example.com/api/webhooks/github
Events:
- issues (opened, edited, deleted, closed, reopened)
- pull_request (opened, edited, closed, merged)
- milestone (created, edited, deleted, closed)
- project (created, edited, deleted)
- discussion (created, edited, deleted)

Webhook Payload:
{
  "action": "edited",
  "issue": {
    "number": 42,
    "title": "Updated Story",
    "labels": [{"name": "devflow-story"}],
    "body": "<!-- devflow-id: story-uuid -->\n...",
    ...
  }
}
```

**2. Polling (Backup - Every 5 minutes)**

For cases where webhooks fail or are missed:

```python
class SyncPoller:
    """Polls external systems for changes."""
    
    def poll_jira_changes(self, user_integration: UserIntegration):
        """Poll Jira for issues updated since last sync."""
        
        # JQL query for recently updated issues
        jql = f"""
        project = PROJ 
        AND updated >= "{user_integration.last_sync_at}"
        AND (
            "DevFlow PRD ID" is not EMPTY
            OR "DevFlow Epic ID" is not EMPTY
            OR "DevFlow Story ID" is not EMPTY
        )
        ORDER BY updated ASC
        """
        
        issues = jira_api.search_issues(jql, max_results=100)
        
        for issue in issues:
            self.sync_jira_issue_to_devflow(issue, user_integration)
        
        user_integration.last_sync_at = datetime.now()
        user_integration.save()
    
    def poll_github_changes(self, user_integration: UserIntegration):
        """Poll GitHub for issues updated since last sync."""
        
        params = {
            "state": "all",
            "since": user_integration.last_sync_at.isoformat(),
            "labels": "devflow-prd,devflow-epic,devflow-story,devflow-task",
            "per_page": 100
        }
        
        issues = github_api.get_issues(params)
        
        for issue in issues:
            self.sync_github_issue_to_devflow(issue, user_integration)
        
        user_integration.last_sync_at = datetime.now()
        user_integration.save()
```

### Sync Data Flow

**DevFlow → External Systems:**

```
┌─────────────────────────────────────────────────────────────┐
│ User creates Story in DevFlow                               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ DevFlow Sync Service validates hierarchy:                  │
│ - Story has Epic parent? ✓                                 │
│ - Epic exists in all enabled integrations? ✓               │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼──────────┐   ┌────────▼──────────┐
│ Create Jira Story │   │ Create GH Issue   │
│ - Set Epic Link   │   │ - Add to Project  │
│ - Set custom IDs  │   │ - Apply labels    │
│ - Store properties│   │ - Add metadata    │
└────────┬──────────┘   └────────┬──────────┘
         │                       │
         └───────────┬───────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ Record sync in sync_log table                              │
│ Update DevFlow entity with external IDs                    │
└─────────────────────────────────────────────────────────────┘
```

**External Systems → DevFlow:**

```
┌─────────────────────────────────────────────────────────────┐
│ Jira webhook: "Story PROJ-123 updated"                     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ DevFlow Webhook Handler extracts:                          │
│ - Jira issue key: PROJ-123                                 │
│ - DevFlow Story ID from custom field                       │
│ - Changes: title, status, assignee                         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ Hierarchy Validation:                                       │
│ - Check if Epic Link changed                               │
│ - If changed, verify new Epic exists in DevFlow            │
│ - If new Epic doesn't exist: REJECT SYNC                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                ┌────┴────┐
                │ Valid?  │
         ┌──────┴──────┬──────────┐
         NO             YES        │
         │                         │
┌────────▼──────────┐   ┌──────────▼─────────┐
│ Create conflict   │   │ Update DevFlow     │
│ Log rejection     │   │ Propagate to GitHub│
│ Notify user       │   │ Record sync        │
└───────────────────┘   └────────────────────┘
```

### Hierarchy Enforcement

**Violation Detection:**

```python
class HierarchyValidator:
    """Enforces DevFlow type hierarchy on external changes."""
    
    VALID_PARENTS = {
        "prd": None,              # PRD has no parent
        "epic": ["prd", None],    # Epic can have PRD parent or be root
        "story": ["epic"],        # Story MUST have Epic parent
        "task": ["story"],        # Task MUST have Story parent
        "subtask": ["task"]       # Subtask MUST have Task parent
    }
    
    def validate_jira_issue(self, jira_issue: dict) -> ValidationResult:
        """
        Validates Jira issue against DevFlow hierarchy rules.
        
        Returns ValidationResult with:
        - is_valid: bool
        - error_message: str (if invalid)
        - suggested_action: str (how to fix)
        """
        
        # Extract DevFlow type from custom field or issue properties
        devflow_type = self._extract_devflow_type(jira_issue)
        
        if not devflow_type:
            # External creation without DevFlow metadata
            return self._handle_external_creation(jira_issue)
        
        # Get parent from Jira
        parent_key = jira_issue.get("fields", {}).get("parent", {}).get("key")
        epic_link = jira_issue.get("fields", {}).get("customfield_10014")  # Epic Link
        
        # Determine actual parent
        if devflow_type == "story":
            parent_ref = epic_link
        elif devflow_type in ["task", "subtask"]:
            parent_ref = parent_key
        else:
            parent_ref = None
        
        # Validate parent exists in DevFlow
        if parent_ref:
            parent_devflow_id = self._get_devflow_id_from_jira_key(parent_ref)
            
            if not parent_devflow_id:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"{devflow_type.title()} parent '{parent_ref}' not found in DevFlow",
                    suggested_action="Create parent in DevFlow first, or link to existing DevFlow parent"
                )
            
            # Validate parent type
            parent_type = self._get_devflow_type(parent_devflow_id)
            valid_parent_types = self.VALID_PARENTS[devflow_type]
            
            if valid_parent_types and parent_type not in valid_parent_types:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"{devflow_type.title()} cannot have {parent_type} as parent. " +
                                 f"Valid parents: {', '.join(valid_parent_types)}",
                    suggested_action=f"Link to a {' or '.join(valid_parent_types)} instead"
                )
        
        elif devflow_type in ["story", "task", "subtask"]:
            # These types REQUIRE a parent
            return ValidationResult(
                is_valid=False,
                error_message=f"{devflow_type.title()} requires a parent",
                suggested_action=f"Link to a {self.VALID_PARENTS[devflow_type][0]}"
            )
        
        return ValidationResult(is_valid=True)
    
    def _handle_external_creation(self, jira_issue: dict) -> ValidationResult:
        """
        Handle case where Jira issue was created without DevFlow metadata.
        This is a STRICT REJECTION - we don't auto-import.
        """
        
        issue_type = jira_issue["fields"]["issuetype"]["name"].lower()
        
        return ValidationResult(
            is_valid=False,
            error_message=f"Jira {issue_type} '{jira_issue['key']}' was created outside DevFlow",
            suggested_action="Create this item in DevFlow first, which will sync to Jira with proper hierarchy",
            rejection_type="external_creation"
        )
```

**Rejection Handling:**

```python
class SyncRejectionHandler:
    """Handles rejected sync attempts."""
    
    def handle_rejection(
        self, 
        validation_result: ValidationResult,
        source: str,  # "jira", "github", "confluence"
        entity_ref: str,  # External entity reference
        user_integration: UserIntegration
    ):
        """
        Records rejection and creates notification for user.
        """
        
        # Log rejection
        conflict = SyncConflict.create(
            user_integration=user_integration,
            source_platform=source,
            source_entity_ref=entity_ref,
            conflict_type="hierarchy_violation",
            error_message=validation_result.error_message,
            suggested_action=validation_result.suggested_action,
            status="pending_resolution",
            detected_at=datetime.now()
        )
        
        # Create notification
        notification = Notification.create(
            user_id=user_integration.user_id,
            type="sync_rejection",
            title=f"Sync rejected: {source} {entity_ref}",
            message=validation_result.error_message,
            action_url=f"/integrations/conflicts/{conflict.id}",
            action_text="Review & Resolve",
            severity="warning"
        )
        
        # Send real-time notification if user is online
        self.websocket_service.send_to_user(
            user_integration.user_id,
            {
                "type": "sync_rejection",
                "conflict_id": str(conflict.id),
                "notification": notification.to_dict()
            }
        )
        
        return conflict
```

### Conflict Resolution

**Conflict Types:**

1. **Hierarchy Violation**: External system has invalid parent-child relationship
2. **Concurrent Edit**: Same entity edited in multiple places simultaneously  
3. **Deleted Entity**: Entity deleted in one system but still exists in others
4. **Type Mismatch**: Issue type changed to incompatible type
5. **Missing Parent**: Parent entity exists in one system but not others

**Conflict Resolution UI:**

```
╔════════════════════════════════════════════════════════════╗
║ Sync Conflicts Dashboard                         [3 Pending]║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║ ⚠️ Hierarchy Violation                          2 hours ago  ║
║ ┌──────────────────────────────────────────────────────────┐║
║ │ Jira Story PROJ-123 has no Epic parent                  │║
║ │                                                          │║
║ │ 📝 Story: "Implement login screen"                      │║
║ │ ❌ Current: No Epic Link                                │║
║ │ ✅ Required: Must link to an Epic                       │║
║ │                                                          │║
║ │ Recommended Action:                                      │║
║ │ Link PROJ-123 to one of these Epics:                    │║
║ │                                                          │║
║ │ 🔘 PROJ-100: "User Authentication Epic"                 │║
║ │    (18 stories, in progress)                            │║
║ │                                                          │║
║ │ 🔘 PROJ-50: "Mobile App UI Epic"                        │║
║ │    (12 stories, in progress)                            │║
║ │                                                          │║
║ │ 🔘 Create new Epic in DevFlow                           │║
║ │    Title: [                                ]            │║
║ │                                                          │║
║ │ 🔘 Keep in Jira only (don't sync to DevFlow)           │║
║ │                                                          │║
║ │ [Resolve Conflict]              [Ignore for Now]        │║
║ └──────────────────────────────────────────────────────────┘║
║                                                              ║
║ ⚙️ Concurrent Edit                              5 hours ago  ║
║ ┌──────────────────────────────────────────────────────────┐║
║ │ Story "API Integration" edited in multiple systems      │║
║ │                                                          │║
║ │ DevFlow:  "Integrate payment API"   (14:30:00)         │║
║ │ Jira:     "Payment gateway API"      (14:28:00)         │║
║ │ GitHub:   "Setup payment API"        (14:25:00)         │║
║ │                                                          │║
║ │ Recommended: Use DevFlow version (most recent)          │║
║ │                                                          │║
║ │ 🔘 Use DevFlow version                                  │║
║ │ 🔘 Use Jira version                                     │║
║ │ 🔘 Use GitHub version                                   │║
║ │ 🔘 Enter custom title: [                        ]      │║
║ │                                                          │║
║ │ [Apply Resolution]                  [View Full Details] │║
║ └──────────────────────────────────────────────────────────┘║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
```

**Conflict Resolution Logic:**

```python
class ConflictResolver:
    """Resolves sync conflicts based on user decisions."""
    
    def resolve_hierarchy_violation(
        self,
        conflict: SyncConflict,
        resolution: dict  # User's resolution choice
    ):
        """
        Resolves hierarchy violation based on user choice.
        
        Resolution options:
        - link_to_parent: Link to existing parent in DevFlow
        - create_parent: Create new parent, then import
        - keep_external: Don't sync to DevFlow, keep in external system only
        """
        
        if resolution["action"] == "link_to_parent":
            # Update external system to link to chosen parent
            parent_id = resolution["parent_id"]
            parent = DevFlowEntity.get(parent_id)
            
            # Get parent's external reference
            if conflict.source_platform == "jira":
                parent_jira_key = parent.get_jira_key()
                
                # Update Jira issue
                jira_api.update_issue(
                    conflict.source_entity_ref,
                    {"fields": {"customfield_10014": parent_jira_key}}  # Epic Link
                )
            
            # Now sync will succeed
            self.retry_sync(conflict)
            
        elif resolution["action"] == "create_parent":
            # Create new parent in DevFlow
            parent = self.create_parent_entity(
                type=resolution["parent_type"],
                title=resolution["parent_title"],
                user=conflict.user_integration.user
            )
            
            # Sync parent to external systems
            self.sync_entity_to_external(parent, conflict.user_integration)
            
            # Link external entity to new parent
            # ... (similar to above)
            
        elif resolution["action"] == "keep_external":
            # Mark as permanently excluded from sync
            ExcludedEntity.create(
                user_integration=conflict.user_integration,
                platform=conflict.source_platform,
                entity_ref=conflict.source_entity_ref,
                reason="user_excluded",
                excluded_at=datetime.now()
            )
        
        # Mark conflict as resolved
        conflict.status = "resolved"
        conflict.resolved_at = datetime.now()
        conflict.resolution = resolution
        conflict.save()
```

---

## Data Models

### Database Schema

```sql
-- Integration mappings between DevFlow and external systems
CREATE TABLE entity_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- DevFlow entity
    devflow_entity_id UUID NOT NULL,
    devflow_entity_type VARCHAR(50) NOT NULL, -- prd, epic, story, task, subtask
    
    -- External system
    platform VARCHAR(50) NOT NULL,  -- jira, confluence, github
    platform_entity_id TEXT NOT NULL,  -- External ID/key
    platform_entity_type VARCHAR(50),  -- issue, page, milestone, discussion
    platform_url TEXT,  -- Direct URL to entity
    
    -- Ownership
    user_integration_id UUID NOT NULL REFERENCES user_integrations(id) ON DELETE CASCADE,
    
    -- Sync status
    sync_status VARCHAR(50) DEFAULT 'synced',  -- synced, pending, error, conflict
    last_synced_at TIMESTAMPTZ,
    sync_error TEXT,
    
    -- Metadata
    metadata JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(devflow_entity_id, platform, user_integration_id),
    UNIQUE(platform, platform_entity_id, user_integration_id)
);

-- Sync operation log
CREATE TABLE sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- What was synced
    entity_mapping_id UUID REFERENCES entity_mappings(id) ON DELETE SET NULL,
    user_integration_id UUID NOT NULL REFERENCES user_integrations(id) ON DELETE CASCADE,
    
    -- Operation details
    operation VARCHAR(50) NOT NULL,  -- create, update, delete
    direction VARCHAR(50) NOT NULL,  -- devflow_to_external, external_to_devflow
    source_platform VARCHAR(50),
    target_platform VARCHAR(50),
    
    -- Changes
    field_changes JSONB,  -- {"title": {"old": "...", "new": "..."}}
    
    -- Status
    status VARCHAR(50) NOT NULL,  -- success, failed, partial
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    
    -- Context
    triggered_by VARCHAR(50),  -- webhook, poll, user_action
    request_id UUID,  -- For tracing
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sync conflicts requiring user resolution
CREATE TABLE sync_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    user_integration_id UUID NOT NULL REFERENCES user_integrations(id) ON DELETE CASCADE,
    entity_mapping_id UUID REFERENCES entity_mappings(id) ON DELETE SET NULL,
    
    -- Conflict details
    conflict_type VARCHAR(50) NOT NULL,  -- hierarchy_violation, concurrent_edit, etc.
    source_platform VARCHAR(50) NOT NULL,
    source_entity_ref TEXT NOT NULL,
    
    error_message TEXT NOT NULL,
    suggested_action TEXT,
    
    -- Conflicting data
    devflow_data JSONB,
    external_data JSONB,
    
    -- Resolution
    status VARCHAR(50) DEFAULT 'pending',  -- pending, resolved, ignored
    resolution JSONB,  -- User's resolution choice
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    
    -- Metadata
    metadata JSONB,
    
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Entities excluded from sync
CREATE TABLE excluded_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    user_integration_id UUID NOT NULL REFERENCES user_integrations(id) ON DELETE CASCADE,
    
    platform VARCHAR(50) NOT NULL,
    entity_ref TEXT NOT NULL,
    entity_type VARCHAR(50),
    
    reason VARCHAR(100),  -- user_excluded, permanent_conflict, etc.
    
    excluded_at TIMESTAMPTZ DEFAULT NOW(),
    excluded_by UUID REFERENCES users(id),
    
    UNIQUE(user_integration_id, platform, entity_ref)
);

-- Webhook registrations
CREATE TABLE webhook_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    user_integration_id UUID NOT NULL REFERENCES user_integrations(id) ON DELETE CASCADE,
    
    platform VARCHAR(50) NOT NULL,
    webhook_id TEXT NOT NULL,  -- ID from external platform
    webhook_url TEXT NOT NULL,
    
    events TEXT[],  -- Subscribed event types
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, failed
    
    last_triggered_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_integration_id, platform)
);

-- Indexes
CREATE INDEX idx_entity_mappings_devflow ON entity_mappings(devflow_entity_id);
CREATE INDEX idx_entity_mappings_platform ON entity_mappings(platform, platform_entity_id);
CREATE INDEX idx_entity_mappings_user ON entity_mappings(user_integration_id);
CREATE INDEX idx_entity_mappings_status ON entity_mappings(sync_status);

CREATE INDEX idx_sync_log_entity ON sync_log(entity_mapping_id);
CREATE INDEX idx_sync_log_user ON sync_log(user_integration_id);
CREATE INDEX idx_sync_log_status ON sync_log(status);
CREATE INDEX idx_sync_log_created ON sync_log(created_at DESC);

CREATE INDEX idx_sync_conflicts_user ON sync_conflicts(user_integration_id);
CREATE INDEX idx_sync_conflicts_status ON sync_conflicts(status);
CREATE INDEX idx_sync_conflicts_detected ON sync_conflicts(detected_at DESC);

CREATE INDEX idx_excluded_entities_user ON excluded_entities(user_integration_id);
```

---

## API Specifications

### Integration Management Endpoints

#### Connect Atlassian

```
POST /api/integrations/atlassian/connect

Initiates Atlassian OAuth flow.

Response:
{
  "oauth_url": "https://auth.atlassian.com/authorize?client_id=...",
  "state": "csrf-token-here"
}
```

#### OAuth Callback

```
GET /api/integrations/atlassian/callback?code=...&state=...

Completes OAuth flow and stores tokens.

Response:
{
  "integration_id": "uuid",
  "cloud_id": "35273b54-3f06-40d2-880f-dd28cf8daafa",
  "site_name": "My Company Jira",
  "site_url": "https://mycompany.atlassian.net",
  "status": "active"
}
```

#### Setup Custom Fields

```
POST /api/integrations/jira/{integration_id}/setup-custom-fields

Creates required DevFlow custom fields in Jira.

Request:
{
  "projects": ["PROJ", "DEV"]  // Optional: specific projects
}

Response:
{
  "created_fields": [
    {
      "name": "DevFlow PRD ID",
      "field_id": "customfield_10050",
      "type": "text"
    },
    {
      "name": "DevFlow Epic ID",
      "field_id": "customfield_10051",
      "type": "text"
    },
    ...
  ],
  "existing_fields": [...]
}
```

#### Configure Space/Project Mapping

```
POST /api/integrations/confluence/{integration_id}/configure-space

Request:
{
  "devflow_project_id": "uuid",
  "action": "use_existing",  // or "create_new"
  "space_key": "DEV",  // Required if use_existing
  "space_name": "DevFlow - Development"  // Required if create_new
}

Response:
{
  "space_id": "123456",
  "space_key": "DEV",
  "space_name": "Development",
  "space_url": "https://mycompany.atlassian.net/wiki/spaces/DEV"
}
```

```
POST /api/integrations/github/{integration_id}/configure-repo

Request:
{
  "devflow_project_id": "uuid",
  "owner": "myorg",
  "repo": "myrepo",
  "create_labels": true,
  "create_projects": true
}

Response:
{
  "repo_id": 123456,
  "full_name": "myorg/myrepo",
  "labels_created": ["devflow-prd", "devflow-epic", ...],
  "projects_created": []
}
```

### Sync Endpoints

#### Manual Sync Trigger

```
POST /api/integrations/sync/trigger

Request:
{
  "entity_id": "uuid",  // DevFlow entity to sync
  "platforms": ["jira", "github"],  // Optional: specific platforms
  "force": false  // Force sync even if no changes
}

Response:
{
  "sync_id": "uuid",
  "status": "in_progress",
  "started_at": "2025-11-18T14:30:00Z",
  "platforms": {
    "jira": {"status": "pending"},
    "github": {"status": "pending"}
  }
}
```

#### Sync Status

```
GET /api/integrations/sync/{sync_id}/status

Response:
{
  "sync_id": "uuid",
  "status": "completed",
  "platforms": {
    "jira": {
      "status": "success",
      "entity_ref": "PROJ-123",
      "synced_at": "2025-11-18T14:30:15Z"
    },
    "github": {
      "status": "success",
      "entity_ref": "42",
      "synced_at": "2025-11-18T14:30:18Z"
    }
  },
  "completed_at": "2025-11-18T14:30:20Z",
  "duration_ms": 5234
}
```

### Conflict Management Endpoints

#### List Conflicts

```
GET /api/integrations/conflicts?status=pending&platform=jira

Response:
{
  "conflicts": [
    {
      "id": "uuid",
      "conflict_type": "hierarchy_violation",
      "source_platform": "jira",
      "source_entity_ref": "PROJ-123",
      "error_message": "Story has no Epic parent",
      "suggested_action": "Link to an Epic",
      "detected_at": "2025-11-18T12:00:00Z",
      "status": "pending"
    }
  ],
  "total": 15,
  "pending": 3
}
```

#### Resolve Conflict

```
POST /api/integrations/conflicts/{conflict_id}/resolve

Request:
{
  "action": "link_to_parent",
  "parent_id": "epic-uuid-here"
}

// OR

{
  "action": "create_parent",
  "parent_type": "epic",
  "parent_title": "User Authentication Epic"
}

// OR

{
  "action": "keep_external"
}

Response:
{
  "conflict_id": "uuid",
  "status": "resolved",
  "resolution": {...},
  "resolved_at": "2025-11-18T14:35:00Z"
}
```

### Webhook Endpoints

#### Jira Webhook Handler

```
POST /api/webhooks/jira
Content-Type: application/json
X-Atlassian-Webhook-Identifier: {webhook_id}

Request Body: [Jira webhook payload]

Response:
{
  "status": "processed",
  "sync_id": "uuid"
}
```

#### GitHub Webhook Handler

```
POST /api/webhooks/github
Content-Type: application/json
X-GitHub-Event: issues
X-Hub-Signature-256: {signature}

Request Body: [GitHub webhook payload]

Response:
{
  "status": "processed",
  "sync_id": "uuid"
}
```

---

## MCP Tools

### Integration Tools for AI Agents

```python
@mcp_tool
async def sync_entity_to_jira(
    entity_id: str,
    force: bool = False
) -> dict:
    """
    Sync a DevFlow entity to Jira.
    
    Args:
        entity_id: DevFlow entity UUID
        force: Force sync even if no changes detected
    
    Returns:
        {
            "jira_key": "PROJ-123",
            "jira_url": "https://...",
            "status": "synced",
            "synced_at": "2025-11-18T14:30:00Z"
        }
    """
    pass

@mcp_tool
async def create_prd_with_integrations(
    title: str,
    description: str,
    confluence_space_key: str,
    jira_project_key: str,
    github_repo: str = None
) -> dict:
    """
    Create PRD in DevFlow and all integrated systems.
    
    Args:
        title: PRD title
        description: PRD description (markdown)
        confluence_space_key: Confluence space to create page in
        jira_project_key: Jira project to create epic in
        github_repo: Optional GitHub repo (format: "owner/repo")
    
    Returns:
        {
            "prd_id": "uuid",
            "confluence_page_id": "123456",
            "jira_epic_key": "PROJ-100",
            "github_milestone_id": 5
        }
    """
    pass

@mcp_tool
async def link_jira_issue_to_devflow(
    jira_key: str,
    parent_id: str = None
) -> dict:
    """
    Import existing Jira issue into DevFlow.
    
    Args:
        jira_key: Jira issue key (e.g., "PROJ-123")
        parent_id: Optional DevFlow parent entity UUID
    
    Returns:
        {
            "devflow_entity_id": "uuid",
            "status": "imported",
            "conflicts": []
        }
    """
    pass

@mcp_tool
async def get_sync_status(entity_id: str) -> dict:
    """
    Get sync status for a DevFlow entity.
    
    Args:
        entity_id: DevFlow entity UUID
    
    Returns:
        {
            "entity_id": "uuid",
            "platforms": {
                "jira": {
                    "synced": true,
                    "entity_ref": "PROJ-123",
                    "last_synced": "2025-11-18T14:30:00Z"
                },
                "github": {...}
            },
            "has_conflicts": false
        }
    """
    pass

@mcp_tool
async def resolve_sync_conflict(
    conflict_id: str,
    resolution_action: str,
    **kwargs
) -> dict:
    """
    Resolve a sync conflict.
    
    Args:
        conflict_id: Conflict UUID
        resolution_action: "link_to_parent", "create_parent", "keep_external"
        **kwargs: Additional args based on resolution_action
    
    Returns:
        {
            "conflict_id": "uuid",
            "status": "resolved",
            "resolution": {...}
        }
    """
    pass
```

---

## Configuration

### Environment Variables

```bash
# Atlassian OAuth
ATLASSIAN_CLIENT_ID=your-oauth-client-id
ATLASSIAN_CLIENT_SECRET=your-oauth-client-secret
ATLASSIAN_REDIRECT_URI=https://devflow.example.com/oauth/atlassian/callback

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-app-id
GITHUB_CLIENT_SECRET=your-github-app-secret
GITHUB_REDIRECT_URI=https://devflow.example.com/oauth/github/callback

# Webhook secrets
JIRA_WEBHOOK_SECRET=random-secret-key
GITHUB_WEBHOOK_SECRET=random-secret-key
CONFLUENCE_WEBHOOK_SECRET=random-secret-key

# Encryption
TOKEN_ENCRYPTION_KEY=256-bit-encryption-key

# Sync settings
SYNC_POLL_INTERVAL_SECONDS=300
SYNC_BATCH_SIZE=50
SYNC_MAX_RETRIES=3
SYNC_RETRY_DELAY_SECONDS=60

# Rate limiting
JIRA_RATE_LIMIT_PER_MINUTE=100
GITHUB_RATE_LIMIT_PER_HOUR=5000
```

### Service Configuration

```yaml
integrations:
  atlassian:
    enabled: true
    priority: 1  # Higher priority than GitHub
    
    oauth:
      scopes:
        - read:jira-work
        - write:jira-work
        - read:confluence-content.all
        - write:confluence-content
        - offline_access
      
    jira:
      custom_fields:
        auto_create: true  # Offer to create when missing
        prefix: "DevFlow"
        
      issue_types:
        prd: "Epic"
        epic: "Epic"
        story: "Story"
        task: "Task"
        subtask: "Sub-task"
      
      webhooks:
        events:
          - jira:issue_created
          - jira:issue_updated
          - jira:issue_deleted
          - jira:issue_link_created
    
    confluence:
      page_templates:
        prd: "devflow-prd-template"
        epic: "devflow-epic-template"
        story: "devflow-story-template"
      
      space_creation:
        allow: true
        prefix: "DevFlow"
        
      webhooks:
        events:
          - page_created
          - page_updated
          - page_removed
  
  github:
    enabled: true
    priority: 2
    
    oauth:
      scopes:
        - repo
        - read:org
        - write:discussion
        - read:project
        - write:project
    
    labels:
      auto_create: true
      prefix: "devflow"
      
    projects:
      use_projects_beta: true
      auto_create_for_epic: true
      
    webhooks:
      events:
        - issues
        - pull_request
        - milestone
        - project
        - discussion
  
  sync:
    strategies:
      primary: "webhooks"
      fallback: "polling"
      
    polling:
      interval_seconds: 300
      batch_size: 50
      
    conflict_resolution:
      strategy: "manual"  # manual, auto_devflow_wins, auto_timestamp_wins
      notification_method: "dashboard"  # dashboard, email, both
      
    hierarchy_enforcement:
      strict_mode: true  # Reject violations
      auto_create_parents: false
      
    retry:
      max_attempts: 3
      delay_seconds: 60
      exponential_backoff: true
```

---

## Success Metrics

### Integration Health

| Metric | Target | Critical |
|--------|--------|----------|
| Sync success rate | > 98% | Yes |
| Webhook delivery rate | > 99% | Yes |
| Avg sync latency | < 5 sec | Yes |
| Conflict rate | < 2% | No |
| Conflict resolution time | < 1 day | No |

### User Experience

| Metric | Target | Critical |
|--------|--------|----------|
| OAuth connection success rate | > 95% | Yes |
| Custom field setup success | > 90% | Yes |
| User satisfaction with sync | > 4/5 | No |
| Support tickets for sync issues | < 5% of users | No |

### Technical Performance

| Metric | Target | Critical |
|--------|--------|----------|
| API response time (p95) | < 500ms | Yes |
| Webhook processing time | < 2 sec | Yes |
| Token refresh success rate | > 99.9% | Yes |
| Database query performance | < 100ms | Yes |

---

## Security Considerations

### OAuth Security

1. **CSRF Protection**: Validate state parameter on OAuth callback
2. **Token Encryption**: AES-256-GCM for stored tokens
3. **Token Rotation**: Refresh tokens proactively before expiration
4. **Scope Minimization**: Request only necessary permissions
5. **Revocation Handling**: Handle token revocation gracefully

### Webhook Security

1. **Signature Validation**: Verify webhook signatures (Jira, GitHub)
2. **Replay Prevention**: Track webhook IDs, reject duplicates
3. **Rate Limiting**: Limit webhook processing rate per integration
4. **IP Allowlisting**: Optional allowlist for webhook sources
5. **Error Handling**: Never expose internal errors in webhook responses

### Data Privacy

1. **User Data Isolation**: Each user's integrations are sandboxed
2. **Minimal Data Storage**: Only store necessary sync metadata
3. **Audit Logging**: Log all integration actions
4. **GDPR Compliance**: Allow users to disconnect and delete integration data
5. **Encryption at Rest**: Encrypt sensitive fields in database

---

## Testing Strategy

### Unit Tests

```python
def test_hierarchy_validator_rejects_story_without_epic():
    validator = HierarchyValidator()
    
    jira_issue = {
        "key": "PROJ-123",
        "fields": {
            "issuetype": {"name": "Story"},
            "customfield_10051": "story-uuid",  # DevFlow Story ID
            # No Epic Link!
        }
    }
    
    result = validator.validate_jira_issue(jira_issue)
    
    assert result.is_valid == False
    assert "requires a parent" in result.error_message
    assert result.suggested_action == "Link to a epic"

def test_oauth_token_refresh():
    integration = create_test_integration(
        token_expires_at=datetime.now() + timedelta(minutes=2)
    )
    
    oauth_service = OAuthService()
    oauth_service.refresh_if_needed(integration)
    
    integration.refresh_from_db()
    assert integration.token_expires_at > datetime.now() + timedelta(minutes=50)

def test_conflict_resolver_links_to_parent():
    conflict = create_test_conflict(
        conflict_type="hierarchy_violation"
    )
    
    resolution = {
        "action": "link_to_parent",
        "parent_id": "epic-uuid"
    }
    
    resolver = ConflictResolver()
    resolver.resolve_hierarchy_violation(conflict, resolution)
    
    assert conflict.status == "resolved"
    # Verify Jira was updated with Epic Link
```

### Integration Tests

```python
@pytest.mark.integration
async def test_end_to_end_prd_creation():
    """Test creating PRD flows to all systems."""
    
    # Setup integrations
    user = create_test_user()
    jira_integration = setup_jira_integration(user)
    confluence_integration = setup_confluence_integration(user)
    github_integration = setup_github_integration(user)
    
    # Create PRD in DevFlow
    prd = await create_prd(
        title="Test PRD",
        description="Test description",
        user=user
    )
    
    # Wait for sync
    await wait_for_sync_completion(prd.id, timeout=30)
    
    # Verify Confluence page created
    confluence_page = await confluence_api.get_page(
        prd.integrations.confluence.page_id
    )
    assert confluence_page["title"] == "Test PRD"
    
    # Verify Jira epic created
    jira_epic = await jira_api.get_issue(
        prd.integrations.jira.issue_key
    )
    assert jira_epic["fields"]["summary"] == "Test PRD"
    assert jira_epic["fields"]["customfield_10050"] == str(prd.id)
    
    # Verify GitHub milestone created
    github_milestone = await github_api.get_milestone(
        prd.integrations.github.milestone_id
    )
    assert github_milestone["title"] == "Test PRD"

@pytest.mark.integration
async def test_hierarchy_violation_rejection():
    """Test that orphaned Story in Jira is rejected."""
    
    user = create_test_user()
    jira_integration = setup_jira_integration(user)
    
    # Create Story in Jira WITHOUT Epic Link
    jira_issue = await jira_api.create_issue({
        "fields": {
            "project": {"key": "TEST"},
            "issuetype": {"name": "Story"},
            "summary": "Orphan Story"
            # No Epic Link or DevFlow metadata
        }
    })
    
    # Trigger webhook
    await send_test_webhook("jira:issue_created", jira_issue)
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Verify conflict was created
    conflicts = await get_conflicts(user, status="pending")
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "external_creation"
    assert jira_issue["key"] in conflicts[0].source_entity_ref
```

### Load Tests

```python
@pytest.mark.load
async def test_concurrent_sync_performance():
    """Test syncing 100 entities concurrently."""
    
    user = create_test_user()
    setup_all_integrations(user)
    
    # Create 100 stories
    stories = [create_test_story(user) for _ in range(100)]
    
    # Sync all concurrently
    start = time.time()
    await asyncio.gather(*[
        sync_entity_to_all_platforms(story) for story in stories
    ])
    duration = time.time() - start
    
    # Should complete within 30 seconds
    assert duration < 30
    
    # All should succeed
    for story in stories:
        assert story.integrations.jira.sync_status == "synced"
        assert story.integrations.github.sync_status == "synced"
```

---

## Future Enhancements

### Phase 1 Enhancements (Q2 2025)

1. **Bitbucket Integration**: Code repository integration with PR linking
2. **Advanced Conflict Resolution**: ML-based resolution suggestions
3. **Bulk Import**: Import existing Jira projects into DevFlow
4. **Custom Field Mapping**: Map DevFlow fields to custom Jira fields

### Phase 2 Enhancements (Q3 2025)

1. **Slack Integration**: Notifications and quick actions
2. **Azure DevOps Integration**: Enterprise alternative to GitHub
3. **Trello/Asana Import**: Migrate from other tools
4. **Workflow Automation**: Trigger DevFlow workflows from external events

### Phase 3 Enhancements (Q4 2025)

1. **Advanced Analytics**: Cross-platform metrics and insights
2. **Custom Integration SDK**: Allow users to build custom integrations
3. **Enterprise SSO**: Integrate with corporate identity providers
4. **Multi-Tenant Support**: Share integrations across organization

---

## Open Questions

1. **Should DevFlow support syncing comments bidirectionally?** Or just link to external comments?

2. **How to handle attachments?** Store in DevFlow, or just link to external attachments?

3. **Should DevFlow create a default Confluence page for every Story?** Or only for complex ones?

4. **GitHub Projects**: Should DevFlow manage multiple projects per repo? Or one project per Epic?

5. **Sync frequency**: Is 5-minute polling sufficient? Or should we support real-time (< 1 min)?

---

**End of PRD-006**
