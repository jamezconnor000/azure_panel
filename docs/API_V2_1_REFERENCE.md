# AetherAccess API v2.1 Reference

## Overview

AetherAccess v2.1 adds comprehensive user management, authentication, door configuration, and access level management to the existing access control system.

**Base URL**: `http://localhost:8080/api/v2.1`

**Authentication**: Bearer token (JWT)

**Total Endpoints**: 30

---

## Authentication Endpoints

### POST `/auth/login`
Login and receive JWT tokens.

**Request**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@aetheraccess.local",
    "role": "admin"
  }
}
```

### POST `/auth/logout`
Logout and invalidate current session.

**Headers**: `Authorization: Bearer <token>`

### POST `/auth/refresh`
Refresh access token using refresh token.

### GET `/auth/me`
Get current user information.

**Headers**: `Authorization: Bearer <token>`

---

## User Management

### POST `/users`
Create a new user (admin only).

**Request**:
```json
{
  "username": "jdoe",
  "email": "john.doe@example.com",
  "password": "securepass123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "phone": "+1-555-0100"
}
```

**Roles**: `admin`, `operator`, `guard`, `user`

### GET `/users`
List all users.

**Query Parameters**:
- `include_inactive` (bool): Include inactive users

### GET `/users/{user_id}`
Get user by ID.

### PUT `/users/{user_id}`
Update user information.

**Request**:
```json
{
  "email": "newemail@example.com",
  "first_name": "Jane",
  "role": "operator"
}
```

### DELETE `/users/{user_id}`
Delete user (soft delete).

### POST `/users/{user_id}/change-password`
Change user password.

**Request**:
```json
{
  "current_password": "oldpass",
  "new_password": "newpass123"
}
```

---

## Door Configuration

### POST `/doors`
Create door configuration.

**Request**:
```json
{
  "door_id": 1,
  "door_name": "Main Entrance",
  "description": "Primary building entrance",
  "location": "Building A - Front",
  "door_type": "entry",
  "osdp_enabled": true,
  "scbk": "0102030405060708090A0B0C0D0E0F10",
  "reader_address": 0,
  "baud_rate": 9600,
  "led_control": true,
  "buzzer_control": true,
  "is_monitored": true,
  "alert_on_failure": true
}
```

**Door Types**: `entry`, `exit`, `interior`, `emergency`

### GET `/doors`
List all door configurations.

### GET `/doors/{door_id}`
Get door configuration.

### PUT `/doors/{door_id}`
Update door configuration.

**Request**:
```json
{
  "door_name": "Main Entrance (Updated)",
  "description": "New description",
  "osdp_enabled": false
}
```

### DELETE `/doors/{door_id}`
Delete door configuration.

### POST `/doors/{door_id}/osdp/enable`
Enable OSDP Secure Channel for a door.

**Request**:
```json
{
  "scbk": "0102030405060708090A0B0C0D0E0F10",
  "reader_address": 0
}
```

**Note**: SCBK must be 32 hexadecimal characters (16 bytes).

### POST `/doors/{door_id}/osdp/disable`
Disable OSDP Secure Channel for a door.

---

## Access Levels

### POST `/access-levels`
Create access level.

**Request**:
```json
{
  "name": "Executive Access",
  "description": "Full access to executive areas",
  "priority": 90
}
```

### GET `/access-levels`
List all access levels.

**Query Parameters**:
- `include_inactive` (bool): Include inactive access levels

### GET `/access-levels/{level_id}`
Get access level.

### PUT `/access-levels/{level_id}`
Update access level.

### DELETE `/access-levels/{level_id}`
Delete access level (soft delete).

### POST `/access-levels/{level_id}/doors`
Add door to access level.

**Request**:
```json
{
  "door_id": 1,
  "timezone_id": 2,
  "entry_allowed": true,
  "exit_allowed": true
}
```

**Timezone IDs**:
- `0`: Null (never)
- `1`: Never
- `2`: Always
- `3+`: Custom timezones (from timezones table)

### DELETE `/access-levels/{level_id}/doors/{door_id}`
Remove door from access level.

### GET `/access-levels/{level_id}/doors`
Get doors for access level.

---

## User Access Level Assignment

### POST `/users/{user_id}/access-levels`
Grant access level to user.

**Request**:
```json
{
  "access_level_id": 1,
  "activation_date": 0,
  "expiration_date": 0,
  "notes": "Granted during onboarding"
}
```

**Dates**: Unix timestamp (0 = immediate/never)

### DELETE `/users/{user_id}/access-levels/{level_id}`
Revoke access level from user.

### GET `/users/{user_id}/access-levels`
Get user's access levels.

### GET `/users/{user_id}/doors`
Get doors user can access (effective permissions).

---

## Audit Logs

### GET `/audit-logs`
Get audit logs with filtering.

**Query Parameters**:
- `limit` (int): Max results (default: 100)
- `offset` (int): Pagination offset
- `user_id` (int): Filter by user
- `action_type` (string): Filter by action
- `start_time` (int): Unix timestamp
- `end_time` (int): Unix timestamp

**Response**:
```json
[
  {
    "id": 123,
    "timestamp": 1699564800,
    "user_id": 1,
    "action_type": "login_success",
    "resource_type": null,
    "resource_id": null,
    "details": "{}",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "success": true
  }
]
```

---

## Role-Based Permissions

### Admin
- Full access to all endpoints
- Can create/modify/delete users, doors, access levels
- Can grant/revoke access
- Can view audit logs

### Operator
- Can read users, doors, access levels
- Can control doors
- Can view audit logs
- Cannot modify configurations

### Guard
- Can read doors
- Can control doors
- Can view audit logs
- Limited administrative access

### User
- Can only view doors
- No control capabilities
- Cannot access administrative functions

---

## Response Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Authentication Flow

1. **Login**: POST `/auth/login` with credentials
2. **Receive Tokens**: Get access_token and refresh_token
3. **Use Token**: Include `Authorization: Bearer <access_token>` header in requests
4. **Refresh Token**: When access_token expires, POST `/auth/refresh` with refresh_token
5. **Logout**: POST `/auth/logout` to invalidate session

---

## Default Credentials

**Username**: `admin`
**Password**: `admin123`

**⚠️ IMPORTANT**: Change the default password immediately in production!

---

## Database Tables

### users
Stores system users with authentication credentials.

### door_configs
Enhanced door configuration with OSDP settings and naming.

### access_levels
Groups of doors for access control.

### access_level_doors
Maps doors to access levels.

### user_access_levels
Maps users to access levels with activation/expiration.

### audit_log
Comprehensive audit trail.

### sessions
Active user sessions for JWT management.

### card_holders
Card holder information (extends cards functionality).

---

## Example Workflows

### Create New User with Door Access

```bash
# 1. Login as admin
TOKEN=$(curl -X POST http://localhost:8080/api/v2.1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# 2. Create user
curl -X POST http://localhost:8080/api/v2.1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jdoe",
    "email": "john@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user"
  }'

# 3. Grant access level to user
curl -X POST http://localhost:8080/api/v2.1/users/2/access-levels \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "access_level_id": 2,
    "activation_date": 0,
    "expiration_date": 0
  }'

# 4. View user's doors
curl http://localhost:8080/api/v2.1/users/2/doors \
  -H "Authorization: Bearer $TOKEN"
```

### Configure Door with OSDP

```bash
# 1. Create door configuration
curl -X POST http://localhost:8080/api/v2.1/doors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "door_id": 10,
    "door_name": "Server Room",
    "location": "Building A - 2nd Floor",
    "door_type": "interior",
    "osdp_enabled": false
  }'

# 2. Enable OSDP Secure Channel
curl -X POST http://localhost:8080/api/v2.1/doors/10/osdp/enable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scbk": "0102030405060708090A0B0C0D0E0F10",
    "reader_address": 0
  }'
```

### Create Access Level with Doors

```bash
# 1. Create access level
curl -X POST http://localhost:8080/api/v2.1/access-levels \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "IT Staff",
    "description": "Access for IT department",
    "priority": 75
  }'

# 2. Add doors to access level
curl -X POST http://localhost:8080/api/v2.1/access-levels/5/doors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "door_id": 1,
    "timezone_id": 2,
    "entry_allowed": true,
    "exit_allowed": true
  }'

curl -X POST http://localhost:8080/api/v2.1/access-levels/5/doors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "door_id": 10,
    "timezone_id": 2,
    "entry_allowed": true,
    "exit_allowed": true
  }'
```

---

## Testing the API

### Using Swagger UI

Visit http://localhost:8080/docs when the server is running for interactive API documentation.

### Using curl

See example workflows above.

### Using Python

```python
import requests

# Login
response = requests.post('http://localhost:8080/api/v2.1/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['access_token']

# Create headers
headers = {'Authorization': f'Bearer {token}'}

# List users
users = requests.get('http://localhost:8080/api/v2.1/users', headers=headers).json()
print(users)

# List doors
doors = requests.get('http://localhost:8080/api/v2.1/doors', headers=headers).json()
print(doors)
```

---

## Integration with Existing API (v1)

The v2.1 API coexists with the existing v1 API:

- **v1**: `/api/v1/...` - Door control, reader health, I/O monitoring
- **v2.1**: `/api/v2.1/...` - User management, authentication, configuration

Both APIs are available simultaneously and work together.

---

## Security Considerations

1. **Change Default Password**: Update the admin password immediately
2. **Use HTTPS**: Enable TLS/SSL in production
3. **Rotate Keys**: Change the SECRET_KEY in auth.py
4. **Rate Limiting**: Implement rate limiting for login attempts
5. **Input Validation**: All inputs are validated via Pydantic models
6. **SQL Injection**: Protected by using parameterized queries
7. **Audit Logging**: All actions are logged to audit_log table

---

## Next Steps

1. Start the backend server
2. Test the API using Swagger UI
3. Build frontend interfaces
4. Customize for your requirements
5. Deploy to production with proper security

---

**AetherAccess v2.1 - Enterprise Access Control with Complete User Management**
