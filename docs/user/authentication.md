# Authentication Guide for Mobile App Developers

## Overview

The Product Finder API uses JWT (JSON Web Token) authentication to secure access to the GraphQL endpoint. This guide explains how to authenticate users from your React Native mobile application.

## Authentication Flow

1. **User Registration** - Create a new user account
2. **User Login** - Obtain JWT access and refresh tokens
3. **Make Authenticated Requests** - Include access token in GraphQL requests
4. **Refresh Tokens** - Get new access token when it expires

## Base URL

Development: `http://localhost:8000`
Production: `https://your-app.run.app` (or your deployed URL)

## API Endpoints

### 1. User Registration

Create a new user account using email and receive JWT tokens.

**Endpoint:** `POST /api/auth/register/`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Success Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "email": "john@example.com"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Error Responses:**
```json
// 400 Bad Request - Missing fields
{
  "error": "email and password are required"
}

// 400 Bad Request - Email exists
{
  "error": "Email already exists"
}
```

### 2. User Login

Login with email and password to obtain JWT tokens.

**Endpoint:** `POST /api/auth/login/`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Success Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "john@example.com"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Error Responses:**
```json
// 400 Bad Request - Missing fields
{
  "error": "email and password are required"
}

// 401 Unauthorized - Invalid credentials
{
  "error": "Invalid credentials"
}

// 401 Unauthorized - Account disabled
{
  "error": "User account is disabled"
}
```

### 3. Token Refresh

Exchange a refresh token for a new access token when the access token expires.

**Endpoint:** `POST /api/auth/refresh/`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Success Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Note:** The response includes both a new access token AND a new refresh token due to token rotation being enabled for security.

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

### 4. Token Verification (Optional)

Verify that a token is valid without making a full request.

**Endpoint:** `POST /api/auth/verify/`

**Request Body:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Success Response (200 OK):**
```json
{}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

### 5. Get User Profile

Get the current authenticated user's profile information.

**Endpoint:** `GET /api/auth/me/`

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "date_joined": "2025-11-19T12:00:00Z"
}
```

## Making Authenticated GraphQL Requests

Once you have an access token, include it in the `Authorization` header for all GraphQL requests.

**Endpoint:** `POST /graphql/`

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Example Request:**
```json
{
  "query": "query { productByUpc(upc: \"012345678901\") { id name brand upcCode } }"
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "productByUpc": {
      "id": 1,
      "name": "Example Product",
      "brand": "Example Brand",
      "upcCode": "012345678901"
    }
  }
}
```

**Error Response (401 Unauthorized) - No token:**
```json
{
  "errors": [
    {
      "message": "Authentication credentials were not provided."
    }
  ]
}
```

**Error Response (401 Unauthorized) - Invalid token:**
```json
{
  "errors": [
    {
      "message": "Authentication failed: Token is invalid or expired"
    }
  ]
}
```

## Token Lifecycle

- **Access Token Lifetime:** 60 minutes (default)
- **Refresh Token Lifetime:** 7 days (default)
- **Token Rotation:** Enabled (new refresh token issued with each refresh request)
- **Blacklisting:** Enabled (old tokens are invalidated after rotation)

## React Native Implementation Example

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://your-app.run.app';

// Store tokens
async function storeTokens(accessToken, refreshToken) {
  await AsyncStorage.setItem('access_token', accessToken);
  await AsyncStorage.setItem('refresh_token', refreshToken);
}

// Get tokens
async function getTokens() {
  const accessToken = await AsyncStorage.getItem('access_token');
  const refreshToken = await AsyncStorage.getItem('refresh_token');
  return { accessToken, refreshToken };
}

// Register new user
async function register(email, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/register/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  
  if (response.ok) {
    await storeTokens(data.tokens.access, data.tokens.refresh);
    return { success: true, user: data.user };
  } else {
    return { success: false, error: data.error };
  }
}

// Login
async function login(email, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  
  if (response.ok) {
    await storeTokens(data.tokens.access, data.tokens.refresh);
    return { success: true, user: data.user };
  } else {
    return { success: false, error: data.error };
  }
}

// Refresh access token
async function refreshAccessToken() {
  const { refreshToken } = await getTokens();
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  const response = await fetch(`${API_BASE_URL}/api/auth/refresh/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  
  const data = await response.json();
  
  if (response.ok) {
    await storeTokens(data.access, data.refresh);
    return data.access;
  } else {
    // Refresh token expired, user needs to login again
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('refresh_token');
    throw new Error('Session expired, please login again');
  }
}

// Make authenticated GraphQL request with auto-retry on token expiration
async function graphqlRequest(query, variables = {}) {
  const { accessToken } = await getTokens();
  
  if (!accessToken) {
    throw new Error('Not authenticated');
  }
  
  const response = await fetch(`${API_BASE_URL}/graphql/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ query, variables }),
  });
  
  // If unauthorized, try to refresh token and retry once
  if (response.status === 401) {
    try {
      const newAccessToken = await refreshAccessToken();
      
      const retryResponse = await fetch(`${API_BASE_URL}/graphql/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${newAccessToken}`,
        },
        body: JSON.stringify({ query, variables }),
      });
      
      return await retryResponse.json();
    } catch (error) {
      // Refresh failed, user needs to login
      throw error;
    }
  }
  
  return await response.json();
}

// Example: Query product by UPC
async function getProductByUpc(upc) {
  const query = `
    query ProductByUpc($upc: String!) {
      productByUpc(upc: $upc) {
        id
        name
        brand
        upcCode
        imageUrl
      }
    }
  `;
  
  const result = await graphqlRequest(query, { upc });
  return result.data?.productByUpc;
}

// Logout
async function logout() {
  await AsyncStorage.removeItem('access_token');
  await AsyncStorage.removeItem('refresh_token');
}
```

## Best Practices

1. **Secure Token Storage**: Use `@react-native-async-storage/async-storage` or secure storage libraries like `react-native-keychain` for storing tokens.

2. **Handle Token Expiration**: Implement automatic token refresh when receiving 401 responses from the API.

3. **Logout on Refresh Failure**: When refresh token expires, clear stored tokens and prompt user to login again.

4. **HTTPS Only**: Always use HTTPS in production to protect tokens in transit.

5. **Token Rotation**: The API uses token rotation - always store the new refresh token returned from refresh requests.

6. **Error Handling**: Properly handle authentication errors and provide clear feedback to users.

7. **Don't Store Passwords**: Never store user passwords locally. Only store JWT tokens.

## Security Considerations

- Access tokens expire after 60 minutes for security
- Refresh tokens expire after 7 days
- Old refresh tokens are blacklisted after rotation
- Always validate SSL certificates in production
- Implement biometric authentication on mobile for better UX

## Troubleshooting

### "Authentication credentials were not provided"
- Ensure you're including the `Authorization: Bearer <token>` header
- Check that the token is not empty or malformed

### "Token is invalid or expired"
- Access token has expired - use refresh endpoint to get a new one
- If refresh token also expired, user needs to login again

### "Invalid credentials"
- Check email and password are correct
- Ensure user account exists and is active

## Support

For questions or issues, please refer to the main project documentation or contact the development team.

