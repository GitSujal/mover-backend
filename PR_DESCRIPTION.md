# Complete authentication system and fix seed script

## Summary
This PR adds a complete authentication system for movers and fixes the database seeding script to be idempotent.

## Changes Made

### 🔐 Authentication System
**New Pages:**
- `/signin` - Login page for mover users with email/password authentication
- `/signup` - Registration page for new mover users

**Auth API Features:**
- ✅ `login()` - Authenticate with email and password
- ✅ `register()` - Create new mover user account
- ✅ `logout()` - Clear tokens and log out
- ✅ `storeTokens()` - Save JWT tokens to localStorage
- ✅ `getAccessToken()` - Retrieve access token
- ✅ Complete TypeScript interfaces for type safety

**API Client Enhancements:**
- ✅ Authorization header interceptor to include JWT token in all requests
- ✅ Updated 401 error handler to clear tokens and redirect to `/signin`
- ✅ Tokens stored in localStorage and sent with all API requests

**UI Improvements:**
- ✅ Added "Sign In" button to homepage header
- ✅ Implemented working sign out functionality in mover sidebar
- ✅ Clean, responsive forms with proper validation
- ✅ Loading states and error handling throughout

**Security Features:**
- JWT tokens stored securely in localStorage
- Authorization header sent with all API requests
- Automatic token validation and expiry handling
- Unauthorized requests redirect to signin
- Password minimum length validation (8 characters)
- Password confirmation matching
- Client-side form validation

### 🔧 Database Seeding Fix
**Problem:** Seed script was failing with duplicate key errors when run multiple times

**Solution:** Made `seed_data.py` idempotent by checking for existing records before creating:
- ✅ Insurance policies - Check by `org_id` and `policy_type`
- ✅ Trucks - Check by `license_plate`
- ✅ Drivers - Check by `drivers_license_number`
- ✅ Pricing configs - Check by `org_id` and `is_active`
- ✅ Bookings - Check by `org_id` and `customer_email`
- ✅ Invoices - Check by `booking_id`
- ✅ Support tickets - Check by `org_id` and `customer_email`

Each function now reports:
- Number of new records created
- Total number of records (including existing)

## Testing

### Authentication Flow
1. Visit `/signup` to create a new account
2. Fill in registration form (org_id is optional)
3. Submit and verify redirect to `/mover` dashboard
4. Click "Sign out" in sidebar
5. Verify redirect to `/signin`
6. Login with credentials
7. Verify access to dashboard

### Seed Script
```bash
# Can now run multiple times without errors
python scripts/seed_data.py
python scripts/seed_data.py  # Second run skips existing records
```

## User Flow

**For New Movers:**
1. Visit `/signup`
2. Create account
3. Automatically logged in and redirected to dashboard
4. Access all mover features

**For Existing Movers:**
1. Visit `/signin`
2. Enter credentials
3. Access dashboard

**Sign Out:**
1. Click "Sign out" in sidebar
2. Tokens cleared
3. Redirected to signin page

## Technical Details

**Authentication:**
- JWT tokens with 15-minute access token expiry
- Refresh token support (7 days)
- Automatic token injection via Axios interceptors
- Client-side token storage in localStorage

**Validation:**
- Email format validation
- Password strength requirements (min 8 chars)
- Password confirmation matching
- Phone number format validation (optional)
- Real-time validation feedback

## Files Changed
- `frontend/src/app/signin/page.tsx` - New signin page
- `frontend/src/app/signup/page.tsx` - New signup page
- `frontend/src/lib/api/auth-api.ts` - Enhanced with login/register/logout
- `frontend/src/lib/api/client.ts` - Added auth interceptors
- `frontend/src/components/mover/Sidebar.tsx` - Added working signout
- `frontend/src/app/page.tsx` - Added signin button to header
- `scripts/seed_data.py` - Made idempotent with duplicate checks

## Status
✅ All features working with real API calls - no mocks or placeholders
✅ Database seed script can be run multiple times safely
✅ Complete authentication flow implemented
✅ Type-safe with full TypeScript support
✅ Proper error handling and loading states
✅ Clean, responsive UI

## Screenshots
### Sign In Page
- Clean, professional login form
- Email and password validation
- Error handling with user-friendly messages
- Loading states during authentication

### Sign Up Page
- Comprehensive registration form
- Password confirmation with visual feedback
- Optional phone and org_id fields
- Link to organization onboarding

### Homepage with Sign In Button
- Sign In button added to header navigation
- Clean integration with existing design

### Mover Dashboard with Sign Out
- Working sign out button in sidebar
- Clears tokens and redirects appropriately
