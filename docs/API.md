# DataBridge Pipeline — API Reference

Base URL: `/api/v1`

All endpoints except `/auth/login` require a Bearer token in the `Authorization` header.

## Authentication

### POST /auth/login
Login with username/password. Returns JWT tokens.

**Request:**
```json
{ "username": "artist1", "password": "artist123" }
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "artist1",
    "display_name": "Sarah Chen",
    "email": "sarah.chen@studio.local",
    "role": "artist",
    "department": "VFX",
    "title": "VFX Artist",
    "is_active": true,
    "shotgrid_user_id": null,
    "last_login": "2026-02-19T10:00:00Z",
    "created_at": "2025-11-01T00:00:00Z"
  }
}
```

**Errors:** `401` Invalid credentials

### GET /auth/me
Get current user profile.

**Response (200):** User object (same as login response `user` field)

**Errors:** `401` No/invalid token, `403` No auth header

### POST /auth/refresh
Refresh access token.

**Request:** `{ "refresh_token": "eyJ..." }`

**Response (200):** Same as login response

### POST /auth/logout
Blacklist the current token.

**Response (200):** `{ "message": "Logged out" }`

---

## Transfers

### POST /transfers/
Create a new transfer. **Auth: Any authenticated user**

**Request:**
```json
{
  "name": "Scene_042_Final_v3",
  "category": "vfx_assets",
  "priority": "normal",
  "notes": "Ready for review",
  "shotgrid_project_id": 100,
  "shotgrid_entity_type": "Shot",
  "shotgrid_entity_id": 1001
}
```

**Response (201):** Full Transfer object with `reference`, `approval_chain`, etc.

### GET /transfers/
List transfers (filtered by role visibility).

**Query params:** `status`, `category`, `search`, `page`, `per_page`

**Response (200):**
```json
{
  "items": [ ...Transfer objects... ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### GET /transfers/stats
Transfer statistics for dashboard.

**Response (200):**
```json
{
  "total": 42,
  "pending": 5,
  "approved": 3,
  "scanning": 2,
  "transferred": 28,
  "rejected": 4,
  "avg_time_hours": 18.5
}
```

### GET /transfers/{id}
Get transfer detail with files and approval chain.

### PUT /transfers/{id}
Update transfer (owner/admin only, pre-approval status).

### DELETE /transfers/{id}
Cancel a transfer (owner/admin only).

### POST /transfers/{id}/upload
Upload files to transfer. **Auth: Owner or Admin**

**Request:** `multipart/form-data` with `files` field (multiple)

**Response (200):** Array of TransferFile objects

### GET /transfers/{id}/files
List files for a transfer.

### DELETE /transfers/{id}/files/{file_id}
Delete a file from a transfer.

---

## Approvals

### GET /approvals/pending
List transfers pending current user's approval. **Auth: Based on role**

### GET /approvals/pending/count
Count of pending approvals. **Response:** `{ "count": 3 }`

### POST /approvals/{transfer_id}/approve
Approve a transfer at the current stage.

**Request:** `{ "comment": "Looks good" }` (comment is optional)

**Response (200):** Updated Transfer object with new status

**Errors:** `403` Wrong role, `400` Wrong status

### POST /approvals/{transfer_id}/reject
Reject a transfer.

**Request:** `{ "reason": "Missing frame range — please re-export" }` (min 10 chars)

**Response (200):** Transfer object with `status: "rejected"`

**Errors:** `422` Reason too short, `403` Wrong role

### GET /approvals/{transfer_id}/chain
Get the 5-stage approval chain for a transfer.

### POST /approvals/{transfer_id}/override
Admin override to force a status. **Auth: Admin only**

**Request:** `{ "target_status": "approved", "reason": "Emergency override" }`

---

## ShotGrid

### GET /shotgrid/projects
List ShotGrid projects. Returns mock data when ShotGrid is disabled.

### GET /shotgrid/projects/{id}/shots
List shots for a project. Optional `?sequence=` filter.

### GET /shotgrid/projects/{id}/assets
List assets for a project. Optional `?asset_type=` filter.

### GET /shotgrid/entities/{type}/{id}/tasks
List tasks for an entity.

### POST /shotgrid/link
Link a transfer to a ShotGrid entity.

**Request:** `{ "transfer_id": 1, "entity_type": "Shot", "entity_id": 1001 }`

---

## Scanning

### POST /scanning/{transfer_id}/start
Start virus scan + checksum calculation. **Auth: Data Team / Admin**

### GET /scanning/{transfer_id}/status
Get scan status details.

### POST /scanning/{transfer_id}/complete
Mark scan as complete and prepare for transfer.

---

## Transfer Operations

### POST /transfer-ops/{transfer_id}/execute
Execute file transfer (rsync/cp). **Auth: IT Team / Admin**

### POST /transfer-ops/{transfer_id}/complete
Trigger post-transfer verification.

---

## Notifications

### GET /notifications/
List notifications for current user. **Query:** `per_page`

**Response (200):**
```json
{
  "items": [ { "id": 1, "type": "approved", "title": "...", "is_read": false, ... } ],
  "total": 15,
  "unread_count": 3
}
```

### GET /notifications/unread/count
**Response:** `{ "count": 3 }`

### PUT /notifications/{id}/read
Mark a notification as read.

### PUT /notifications/read-all
Mark all notifications as read.

---

## Activity Log

### GET /activity/
List transfer history entries.

**Query params:** `transfer_id`, `user_id`, `action`, `search`, `page`, `per_page`

**Response (200):**
```json
{
  "items": [ { "id": 1, "transfer_id": 1, "action": "approved", "description": "...", ... } ],
  "total": 100,
  "page": 1,
  "pages": 4
}
```

---

## Error Codes

| Code | Meaning                                  |
|------|------------------------------------------|
| 200  | Success                                  |
| 201  | Created                                  |
| 400  | Bad request / invalid state transition   |
| 401  | Not authenticated / invalid token        |
| 403  | Forbidden / insufficient role            |
| 404  | Resource not found                       |
| 422  | Validation error (Pydantic)              |
| 500  | Internal server error                    |

## Enums

### UserRole
`artist`, `team_lead`, `supervisor`, `line_producer`, `data_team`, `it_team`, `admin`

### TransferStatus
`uploaded`, `pending_team_lead`, `pending_supervisor`, `pending_line_producer`, `approved`, `scanning`, `scan_passed`, `scan_failed`, `copying`, `ready_for_transfer`, `transferring`, `verifying`, `transferred`, `rejected`, `cancelled`

### TransferPriority
`low`, `normal`, `high`, `urgent`

### TransferCategory
`vfx_assets`, `animation`, `textures`, `lighting`, `compositing`, `audio`, `editorial`, `matchmove`, `fx`, `other`
