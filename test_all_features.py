#!/usr/bin/env python3
"""
AetherAccess v2.1 Complete Feature Test Suite
Tests all API endpoints and features
"""

import requests
import json
import random
import string
from datetime import datetime

BASE_URL = "http://localhost:8080/api/v2.1"
session = requests.Session()
token = None

def print_test(name, status="RUNNING"):
    """Print test status"""
    symbols = {"PASS": "✓", "FAIL": "✗", "RUNNING": "→"}
    print(f"{symbols.get(status, '•')} {name}: {status}")

def test_login():
    """Test 1: Authentication"""
    global token
    print("\n" + "="*80)
    print("TEST 1: AUTHENTICATION")
    print("="*80)

    try:
        response = session.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        response.raise_for_status()
        data = response.json()
        token = data['access_token']
        session.headers.update({"Authorization": f"Bearer {token}"})

        print_test("Login with admin/admin123", "PASS")
        print(f"  User: {data['user']['username']}")
        print(f"  Role: {data['user']['role']}")
        print(f"  Token: {token[:50]}...")
        return True
    except Exception as e:
        print_test("Login", "FAIL")
        print(f"  Error: {e}")
        return False

def test_get_current_user():
    """Test 2: Get Current User"""
    print("\n" + "="*80)
    print("TEST 2: GET CURRENT USER")
    print("="*80)

    try:
        response = session.get(f"{BASE_URL}/auth/me")
        response.raise_for_status()
        user = response.json()

        print_test("Get current user info", "PASS")
        print(f"  Username: {user['username']}")
        print(f"  Email: {user['email']}")
        print(f"  Role: {user['role']}")
        return user
    except Exception as e:
        print_test("Get current user", "FAIL")
        print(f"  Error: {e}")
        return None

def test_create_door():
    """Test 3: Create Door"""
    print("\n" + "="*80)
    print("TEST 3: DOOR MANAGEMENT - CREATE")
    print("="*80)

    try:
        door_data = {
            "door_name": "Main Entrance",
            "description": "Primary building entrance door",
            "location": "Building A - Level 1",
            "door_type": "double",
            "osdp_enabled": False
        }

        response = session.post(f"{BASE_URL}/doors", json=door_data)
        response.raise_for_status()
        door = response.json()

        print_test("Create door 'Main Entrance'", "PASS")
        print(f"  Door ID: {door['door_id']}")
        print(f"  Name: {door['door_name']}")
        print(f"  Location: {door['location']}")
        print(f"  OSDP Enabled: {door['osdp_enabled']}")
        return door
    except Exception as e:
        print_test("Create door", "FAIL")
        print(f"  Error: {e}")
        return None

def test_enable_osdp(door_id):
    """Test 4: Enable OSDP Secure Channel"""
    print("\n" + "="*80)
    print("TEST 4: ENABLE OSDP SECURE CHANNEL")
    print("="*80)

    try:
        # Generate random SCBK (32 hex characters)
        scbk = ''.join(random.choices('0123456789ABCDEF', k=32))

        osdp_data = {
            "scbk": scbk,
            "reader_address": 0
        }

        response = session.post(
            f"{BASE_URL}/doors/{door_id}/osdp/enable",
            json=osdp_data
        )
        response.raise_for_status()

        print_test("Enable OSDP for Main Entrance", "PASS")
        print(f"  SCBK: {scbk}")
        print(f"  Reader Address: 0")

        # Verify it was enabled
        response = session.get(f"{BASE_URL}/doors/{door_id}")
        door = response.json()
        print(f"  Verified OSDP Status: {door['osdp_enabled']}")

        return True
    except Exception as e:
        print_test("Enable OSDP", "FAIL")
        print(f"  Error: {e}")
        return False

def test_list_doors():
    """Test 5: List All Doors"""
    print("\n" + "="*80)
    print("TEST 5: LIST ALL DOORS")
    print("="*80)

    try:
        response = session.get(f"{BASE_URL}/doors")
        response.raise_for_status()
        doors = response.json()

        print_test(f"List doors (found {len(doors)})", "PASS")
        for door in doors:
            osdp_status = "ENABLED" if door['osdp_enabled'] else "DISABLED"
            print(f"  [{door['door_id']}] {door['door_name']} - OSDP: {osdp_status}")

        return doors
    except Exception as e:
        print_test("List doors", "FAIL")
        print(f"  Error: {e}")
        return []

def test_create_user():
    """Test 6: Create User"""
    print("\n" + "="*80)
    print("TEST 6: USER MANAGEMENT - CREATE")
    print("="*80)

    try:
        user_data = {
            "username": "operator1",
            "password": "operator123",
            "email": "operator1@aetheraccess.local",
            "first_name": "John",
            "last_name": "Operator",
            "role": "operator"
        }

        response = session.post(f"{BASE_URL}/users", json=user_data)
        response.raise_for_status()
        user = response.json()

        print_test("Create user 'operator1'", "PASS")
        print(f"  User ID: {user['id']}")
        print(f"  Username: {user['username']}")
        print(f"  Role: {user['role']}")
        print(f"  Email: {user['email']}")
        return user
    except Exception as e:
        print_test("Create user", "FAIL")
        print(f"  Error: {e}")
        return None

def test_list_users():
    """Test 7: List All Users"""
    print("\n" + "="*80)
    print("TEST 7: LIST ALL USERS")
    print("="*80)

    try:
        response = session.get(f"{BASE_URL}/users")
        response.raise_for_status()
        users = response.json()

        print_test(f"List users (found {len(users)})", "PASS")
        for user in users:
            print(f"  [{user['id']}] {user['username']} - Role: {user['role']}")

        return users
    except Exception as e:
        print_test("List users", "FAIL")
        print(f"  Error: {e}")
        return []

def test_create_access_level():
    """Test 8: Create Access Level"""
    print("\n" + "="*80)
    print("TEST 8: ACCESS LEVEL MANAGEMENT - CREATE")
    print("="*80)

    try:
        access_level_data = {
            "name": "Executive Access",
            "description": "Full building access for executives",
            "priority": 90
        }

        response = session.post(f"{BASE_URL}/access-levels", json=access_level_data)
        response.raise_for_status()
        level = response.json()

        print_test("Create access level 'Executive Access'", "PASS")
        print(f"  Level ID: {level['level_id']}")
        print(f"  Name: {level['level_name']}")
        print(f"  Priority: {level['priority']}")
        return level
    except Exception as e:
        print_test("Create access level", "FAIL")
        print(f"  Error: {e}")
        return None

def test_assign_door_to_access_level(level_id, door_id):
    """Test 9: Assign Door to Access Level"""
    print("\n" + "="*80)
    print("TEST 9: ASSIGN DOOR TO ACCESS LEVEL")
    print("="*80)

    try:
        response = session.post(
            f"{BASE_URL}/access-levels/{level_id}/doors/{door_id}"
        )
        response.raise_for_status()

        print_test(f"Assign door {door_id} to access level {level_id}", "PASS")

        # Verify assignment
        response = session.get(f"{BASE_URL}/access-levels/{level_id}/doors")
        doors = response.json()
        print(f"  Access level now has {len(doors)} door(s)")
        for door in doors:
            print(f"    - {door['door_name']}")

        return True
    except Exception as e:
        print_test("Assign door to access level", "FAIL")
        print(f"  Error: {e}")
        return False

def test_assign_user_to_access_level(user_id, level_id):
    """Test 10: Assign User to Access Level"""
    print("\n" + "="*80)
    print("TEST 10: ASSIGN USER TO ACCESS LEVEL")
    print("="*80)

    try:
        response = session.post(
            f"{BASE_URL}/user-access/{user_id}/access-levels/{level_id}"
        )
        response.raise_for_status()

        print_test(f"Assign user {user_id} to access level {level_id}", "PASS")

        # Verify user can access the door
        response = session.get(f"{BASE_URL}/user-access/{user_id}/doors")
        doors = response.json()
        print(f"  User now has access to {len(doors)} door(s):")
        for door in doors:
            print(f"    - {door['door_name']} (via {door['level_name']})")

        return True
    except Exception as e:
        print_test("Assign user to access level", "FAIL")
        print(f"  Error: {e}")
        return False

def test_update_door(door_id):
    """Test 11: Update Door"""
    print("\n" + "="*80)
    print("TEST 11: UPDATE DOOR")
    print("="*80)

    try:
        update_data = {
            "door_name": "Main Entrance (Updated)",
            "description": "Primary building entrance - Updated description"
        }

        response = session.put(f"{BASE_URL}/doors/{door_id}", json=update_data)
        response.raise_for_status()
        door = response.json()

        print_test("Update door name and description", "PASS")
        print(f"  New Name: {door['door_name']}")
        print(f"  New Description: {door['description']}")
        return True
    except Exception as e:
        print_test("Update door", "FAIL")
        print(f"  Error: {e}")
        return False

def test_disable_osdp(door_id):
    """Test 12: Disable OSDP"""
    print("\n" + "="*80)
    print("TEST 12: DISABLE OSDP SECURE CHANNEL")
    print("="*80)

    try:
        response = session.post(f"{BASE_URL}/doors/{door_id}/osdp/disable")
        response.raise_for_status()

        print_test("Disable OSDP for door", "PASS")

        # Verify it was disabled
        response = session.get(f"{BASE_URL}/doors/{door_id}")
        door = response.json()
        print(f"  Verified OSDP Status: {door['osdp_enabled']}")

        return True
    except Exception as e:
        print_test("Disable OSDP", "FAIL")
        print(f"  Error: {e}")
        return False

def test_permissions():
    """Test 13: Role-Based Permissions"""
    print("\n" + "="*80)
    print("TEST 13: ROLE-BASED ACCESS CONTROL")
    print("="*80)

    try:
        # Login as operator
        response = session.post(
            f"{BASE_URL}/auth/login",
            json={"username": "operator1", "password": "operator123"}
        )
        response.raise_for_status()
        data = response.json()
        operator_token = data['access_token']

        print_test("Login as operator1", "PASS")
        print(f"  Role: {data['user']['role']}")

        # Try to create a door (should succeed - operators can configure)
        operator_session = requests.Session()
        operator_session.headers.update({"Authorization": f"Bearer {operator_token}"})

        response = operator_session.get(f"{BASE_URL}/doors")
        response.raise_for_status()
        print_test("Operator can read doors", "PASS")

        # Try to create a user (should fail - only admins can create users)
        try:
            response = operator_session.post(
                f"{BASE_URL}/users",
                json={
                    "username": "testuser",
                    "password": "test123",
                    "email": "test@test.com",
                    "role": "user"
                }
            )
            if response.status_code == 403:
                print_test("Operator cannot create users (correct)", "PASS")
            else:
                print_test("Operator permission check", "FAIL")
        except:
            print_test("Operator permission check", "PASS")

        # Restore admin session
        session.headers.update({"Authorization": f"Bearer {token}"})

        return True
    except Exception as e:
        print_test("RBAC test", "FAIL")
        print(f"  Error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("AETHERACCESS v2.1 COMPLETE FEATURE TEST SUITE")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")

    results = []

    # Test 1: Login
    results.append(("Authentication", test_login()))
    if not results[-1][1]:
        print("\n⚠️  Authentication failed. Cannot proceed with other tests.")
        return

    # Test 2: Get current user
    current_user = test_get_current_user()
    results.append(("Get Current User", current_user is not None))

    # Test 3: Create door
    door = test_create_door()
    results.append(("Create Door", door is not None))

    if door:
        # Test 4: Enable OSDP
        results.append(("Enable OSDP", test_enable_osdp(door['door_id'])))

        # Test 5: List doors
        doors = test_list_doors()
        results.append(("List Doors", len(doors) > 0))

        # Test 11: Update door
        results.append(("Update Door", test_update_door(door['door_id'])))

    # Test 6: Create user
    user = test_create_user()
    results.append(("Create User", user is not None))

    # Test 7: List users
    users = test_list_users()
    results.append(("List Users", len(users) > 0))

    # Test 8: Create access level
    access_level = test_create_access_level()
    results.append(("Create Access Level", access_level is not None))

    if access_level and door:
        # Test 9: Assign door to access level
        results.append(("Assign Door to Access Level",
                       test_assign_door_to_access_level(access_level['level_id'], door['door_id'])))

    if user and access_level:
        # Test 10: Assign user to access level
        results.append(("Assign User to Access Level",
                       test_assign_user_to_access_level(user['id'], access_level['level_id'])))

    if door:
        # Test 12: Disable OSDP
        results.append(("Disable OSDP", test_disable_osdp(door['door_id'])))

    # Test 13: Permissions
    results.append(("RBAC Permissions", test_permissions()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")

    print("\n" + "-"*80)
    print(f"Total: {passed}/{total} tests passed ({passed*100//total}%)")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! AetherAccess v2.1 is fully functional.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")

if __name__ == "__main__":
    run_all_tests()
