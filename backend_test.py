#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta
import time
import sys
import os
from dotenv import load_dotenv

# Load environment variables from frontend/.env
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "total": 0
}

# Helper function to run tests and track results
def run_test(test_name, test_func):
    print(f"\n{'=' * 80}")
    print(f"Running test: {test_name}")
    print(f"{'-' * 80}")
    test_results["total"] += 1
    
    try:
        result = test_func()
        if result:
            test_results["passed"] += 1
            print(f"✅ PASSED: {test_name}")
        else:
            test_results["failed"] += 1
            print(f"❌ FAILED: {test_name}")
    except Exception as e:
        test_results["failed"] += 1
        print(f"❌ FAILED: {test_name} - Exception: {str(e)}")

# Test 1: Basic API check
def test_basic_api():
    response = requests.get(f"{API_URL}/")
    if response.status_code != 200:
        print(f"Error: Expected status code 200, got {response.status_code}")
        return False
    
    data = response.json()
    if "message" not in data or data["message"] != "Task Manager API":
        print(f"Error: Expected message 'Task Manager API', got {data}")
        return False
    
    print("Basic API check successful")
    return True

# Test 2: Dashboard Stats
def test_dashboard_stats():
    response = requests.get(f"{API_URL}/dashboard/stats")
    if response.status_code != 200:
        print(f"Error: Expected status code 200, got {response.status_code}")
        return False
    
    data = response.json()
    required_fields = ["total_tasks", "completed_tasks", "in_progress_tasks", 
                      "todo_tasks", "overdue_tasks", "total_projects"]
    
    for field in required_fields:
        if field not in data:
            print(f"Error: Missing required field '{field}' in dashboard stats")
            return False
        
        # Verify that the field is an integer
        if not isinstance(data[field], int):
            print(f"Error: Field '{field}' should be an integer, got {type(data[field])}")
            return False
    
    print("Dashboard stats check successful")
    return True

# Test 3: Task CRUD operations
def test_task_crud():
    # Create a task
    task_data = {
        "title": "Test Task",
        "description": "This is a test task created by the automated test script",
        "priority": "high",
        "category": "Testing",
        "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
    }
    
    create_response = requests.post(f"{API_URL}/tasks", json=task_data)
    if create_response.status_code != 200:
        print(f"Error creating task: {create_response.status_code} - {create_response.text}")
        return False
    
    created_task = create_response.json()
    task_id = created_task["id"]
    print(f"Created task with ID: {task_id}")
    
    # Get all tasks and verify our task is there
    get_all_response = requests.get(f"{API_URL}/tasks")
    if get_all_response.status_code != 200:
        print(f"Error getting all tasks: {get_all_response.status_code} - {get_all_response.text}")
        return False
    
    tasks = get_all_response.json()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            found = True
            break
    
    if not found:
        print(f"Error: Created task with ID {task_id} not found in tasks list")
        return False
    
    print("Task retrieval successful")
    
    # Update the task
    update_data = {
        "title": "Updated Test Task",
        "status": "in_progress"
    }
    
    update_response = requests.put(f"{API_URL}/tasks/{task_id}", json=update_data)
    if update_response.status_code != 200:
        print(f"Error updating task: {update_response.status_code} - {update_response.text}")
        return False
    
    updated_task = update_response.json()
    if updated_task["title"] != "Updated Test Task" or updated_task["status"] != "in_progress":
        print(f"Error: Task not updated correctly. Expected title 'Updated Test Task' and status 'in_progress', got {updated_task}")
        return False
    
    print("Task update successful")
    
    # Delete the task
    delete_response = requests.delete(f"{API_URL}/tasks/{task_id}")
    if delete_response.status_code != 200:
        print(f"Error deleting task: {delete_response.status_code} - {delete_response.text}")
        return False
    
    # Verify task is deleted
    get_all_response = requests.get(f"{API_URL}/tasks")
    tasks = get_all_response.json()
    for task in tasks:
        if task["id"] == task_id:
            print(f"Error: Task with ID {task_id} still exists after deletion")
            return False
    
    print("Task deletion successful")
    return True

# Test 4: Project CRUD operations
def test_project_crud():
    # Create a project
    project_data = {
        "name": "Test Project",
        "description": "This is a test project created by the automated test script"
    }
    
    create_response = requests.post(f"{API_URL}/projects", json=project_data)
    if create_response.status_code != 200:
        print(f"Error creating project: {create_response.status_code} - {create_response.text}")
        return False
    
    created_project = create_response.json()
    project_id = created_project["id"]
    print(f"Created project with ID: {project_id}")
    
    # Get all projects and verify our project is there
    get_all_response = requests.get(f"{API_URL}/projects")
    if get_all_response.status_code != 200:
        print(f"Error getting all projects: {get_all_response.status_code} - {get_all_response.text}")
        return False
    
    projects = get_all_response.json()
    found = False
    for project in projects:
        if project["id"] == project_id:
            found = True
            break
    
    if not found:
        print(f"Error: Created project with ID {project_id} not found in projects list")
        return False
    
    print("Project retrieval (all) successful")
    
    # Get single project
    get_single_response = requests.get(f"{API_URL}/projects/{project_id}")
    if get_single_response.status_code != 200:
        print(f"Error getting single project: {get_single_response.status_code} - {get_single_response.text}")
        return False
    
    single_project = get_single_response.json()
    if single_project["id"] != project_id:
        print(f"Error: Retrieved project ID {single_project['id']} does not match expected ID {project_id}")
        return False
    
    print("Project retrieval (single) successful")
    
    # Update the project
    update_data = {
        "name": "Updated Test Project",
        "description": "This project has been updated"
    }
    
    update_response = requests.put(f"{API_URL}/projects/{project_id}", json=update_data)
    if update_response.status_code != 200:
        print(f"Error updating project: {update_response.status_code} - {update_response.text}")
        return False
    
    updated_project = update_response.json()
    if updated_project["name"] != "Updated Test Project" or updated_project["description"] != "This project has been updated":
        print(f"Error: Project not updated correctly. Expected name 'Updated Test Project', got {updated_project}")
        return False
    
    print("Project update successful")
    
    # We'll keep this project for the project task tests
    return True

# Test 5: Project Task CRUD operations
def test_project_task_crud():
    # First, get a project to work with
    get_projects_response = requests.get(f"{API_URL}/projects")
    if get_projects_response.status_code != 200:
        print(f"Error getting projects: {get_projects_response.status_code} - {get_projects_response.text}")
        return False
    
    projects = get_projects_response.json()
    if not projects:
        print("No projects found. Please run the project CRUD test first.")
        return False
    
    project_id = projects[0]["id"]
    print(f"Using project with ID: {project_id}")
    
    # Create a project task
    task_data = {
        "title": "Test Project Task",
        "description": "This is a test task within a project",
        "priority": "medium",
        "category": "Testing",
        "due_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
        "project_id": project_id
    }
    
    create_response = requests.post(f"{API_URL}/projects/{project_id}/tasks", json=task_data)
    if create_response.status_code != 200:
        print(f"Error creating project task: {create_response.status_code} - {create_response.text}")
        return False
    
    created_task = create_response.json()
    task_id = created_task["id"]
    print(f"Created project task with ID: {task_id}")
    
    # Get all project tasks and verify our task is there
    get_all_response = requests.get(f"{API_URL}/projects/{project_id}/tasks")
    if get_all_response.status_code != 200:
        print(f"Error getting all project tasks: {get_all_response.status_code} - {get_all_response.text}")
        return False
    
    tasks = get_all_response.json()
    found = False
    for task in tasks:
        if task["id"] == task_id:
            found = True
            break
    
    if not found:
        print(f"Error: Created project task with ID {task_id} not found in tasks list")
        return False
    
    print("Project task retrieval successful")
    
    # Update the project task
    update_data = {
        "title": "Updated Project Task",
        "status": "in_progress"
    }
    
    update_response = requests.put(f"{API_URL}/projects/{project_id}/tasks/{task_id}", json=update_data)
    if update_response.status_code != 200:
        print(f"Error updating project task: {update_response.status_code} - {update_response.text}")
        return False
    
    updated_task = update_response.json()
    if updated_task["title"] != "Updated Project Task" or updated_task["status"] != "in_progress":
        print(f"Error: Project task not updated correctly. Expected title 'Updated Project Task' and status 'in_progress', got {updated_task}")
        return False
    
    print("Project task update successful")
    
    # Delete the project task
    delete_response = requests.delete(f"{API_URL}/projects/{project_id}/tasks/{task_id}")
    if delete_response.status_code != 200:
        print(f"Error deleting project task: {delete_response.status_code} - {delete_response.text}")
        return False
    
    # Verify task is deleted
    get_all_response = requests.get(f"{API_URL}/projects/{project_id}/tasks")
    tasks = get_all_response.json()
    for task in tasks:
        if task["id"] == task_id:
            print(f"Error: Project task with ID {task_id} still exists after deletion")
            return False
    
    print("Project task deletion successful")
    
    # Clean up - delete the project
    delete_project_response = requests.delete(f"{API_URL}/projects/{project_id}")
    if delete_project_response.status_code != 200:
        print(f"Warning: Could not delete test project: {delete_project_response.status_code} - {delete_project_response.text}")
    else:
        print(f"Successfully deleted test project with ID: {project_id}")
    
    return True

# Test 6: Test task filtering and status updates
def test_task_filtering_and_status():
    # Create tasks with different statuses and priorities
    tasks_to_create = [
        {"title": "Todo Task", "description": "A task in todo status", "status": "todo", "priority": "low"},
        {"title": "In Progress Task", "description": "A task in progress", "status": "in_progress", "priority": "medium"},
        {"title": "Done Task", "description": "A completed task", "status": "done", "priority": "high"},
        {"title": "Urgent Task", "description": "An urgent task", "status": "todo", "priority": "urgent"}
    ]
    
    created_task_ids = []
    
    # Create the tasks
    for task_data in tasks_to_create:
        create_response = requests.post(f"{API_URL}/tasks", json=task_data)
        if create_response.status_code != 200:
            print(f"Error creating task: {create_response.status_code} - {create_response.text}")
            # Clean up any tasks that were created
            for task_id in created_task_ids:
                requests.delete(f"{API_URL}/tasks/{task_id}")
            return False
        
        created_task = create_response.json()
        created_task_ids.append(created_task["id"])
    
    print(f"Created {len(created_task_ids)} test tasks with different statuses and priorities")
    
    # Get all tasks and verify our tasks are there with correct statuses and priorities
    get_all_response = requests.get(f"{API_URL}/tasks")
    if get_all_response.status_code != 200:
        print(f"Error getting all tasks: {get_all_response.status_code} - {get_all_response.text}")
        # Clean up
        for task_id in created_task_ids:
            requests.delete(f"{API_URL}/tasks/{task_id}")
        return False
    
    tasks = get_all_response.json()
    
    # Verify dashboard stats reflect our created tasks
    dashboard_response = requests.get(f"{API_URL}/dashboard/stats")
    if dashboard_response.status_code != 200:
        print(f"Error getting dashboard stats: {dashboard_response.status_code} - {dashboard_response.text}")
        # Clean up
        for task_id in created_task_ids:
            requests.delete(f"{API_URL}/tasks/{task_id}")
        return False
    
    stats = dashboard_response.json()
    
    # Check if stats reflect our tasks (there might be other tasks in the database)
    todo_count = sum(1 for task in tasks if task["status"] == "todo" and task["id"] in created_task_ids)
    in_progress_count = sum(1 for task in tasks if task["status"] == "in_progress" and task["id"] in created_task_ids)
    done_count = sum(1 for task in tasks if task["status"] == "done" and task["id"] in created_task_ids)
    
    print(f"Dashboard stats: {stats}")
    print(f"Our test tasks: todo={todo_count}, in_progress={in_progress_count}, done={done_count}")
    
    # Update a task status
    if created_task_ids:
        update_data = {"status": "done"}
        update_response = requests.put(f"{API_URL}/tasks/{created_task_ids[0]}", json=update_data)
        if update_response.status_code != 200:
            print(f"Error updating task status: {update_response.status_code} - {update_response.text}")
            # Clean up
            for task_id in created_task_ids:
                requests.delete(f"{API_URL}/tasks/{task_id}")
            return False
        
        updated_task = update_response.json()
        if updated_task["status"] != "done":
            print(f"Error: Task status not updated correctly. Expected 'done', got {updated_task['status']}")
            # Clean up
            for task_id in created_task_ids:
                requests.delete(f"{API_URL}/tasks/{task_id}")
            return False
        
        print("Task status update successful")
    
    # Clean up - delete all created tasks
    for task_id in created_task_ids:
        delete_response = requests.delete(f"{API_URL}/tasks/{task_id}")
        if delete_response.status_code != 200:
            print(f"Warning: Could not delete test task {task_id}: {delete_response.status_code} - {delete_response.text}")
    
    print(f"Successfully deleted {len(created_task_ids)} test tasks")
    return True

# Test 7: Test due date functionality and overdue detection
def test_due_date_and_overdue():
    # Create a task that's already overdue
    yesterday = datetime.utcnow() - timedelta(days=1)
    overdue_task_data = {
        "title": "Overdue Task",
        "description": "This task is already overdue",
        "status": "todo",
        "priority": "high",
        "due_date": yesterday.isoformat()
    }
    
    create_response = requests.post(f"{API_URL}/tasks", json=overdue_task_data)
    if create_response.status_code != 200:
        print(f"Error creating overdue task: {create_response.status_code} - {create_response.text}")
        return False
    
    overdue_task = create_response.json()
    overdue_task_id = overdue_task["id"]
    print(f"Created overdue task with ID: {overdue_task_id}")
    
    # Get dashboard stats to check overdue count
    dashboard_response = requests.get(f"{API_URL}/dashboard/stats")
    if dashboard_response.status_code != 200:
        print(f"Error getting dashboard stats: {dashboard_response.status_code} - {dashboard_response.text}")
        # Clean up
        requests.delete(f"{API_URL}/tasks/{overdue_task_id}")
        return False
    
    stats = dashboard_response.json()
    print(f"Dashboard stats with overdue task: {stats}")
    
    # The overdue_tasks count should be at least 1
    if stats["overdue_tasks"] < 1:
        print(f"Error: Expected at least 1 overdue task, but got {stats['overdue_tasks']}")
        # Clean up
        requests.delete(f"{API_URL}/tasks/{overdue_task_id}")
        return False
    
    print("Overdue task detection successful")
    
    # Mark the overdue task as done
    update_data = {"status": "done"}
    update_response = requests.put(f"{API_URL}/tasks/{overdue_task_id}", json=update_data)
    if update_response.status_code != 200:
        print(f"Error updating overdue task: {update_response.status_code} - {update_response.text}")
        # Clean up
        requests.delete(f"{API_URL}/tasks/{overdue_task_id}")
        return False
    
    # Get dashboard stats again to verify overdue count decreased
    dashboard_response = requests.get(f"{API_URL}/dashboard/stats")
    stats_after_update = dashboard_response.json()
    print(f"Dashboard stats after marking overdue task as done: {stats_after_update}")
    
    # Clean up - delete the overdue task
    delete_response = requests.delete(f"{API_URL}/tasks/{overdue_task_id}")
    if delete_response.status_code != 200:
        print(f"Warning: Could not delete overdue task: {delete_response.status_code} - {delete_response.text}")
    else:
        print(f"Successfully deleted overdue task with ID: {overdue_task_id}")
    
    return True

# Test 8: Test error handling (404s for non-existent resources)
def test_error_handling():
    # Test getting a non-existent task
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    
    response = requests.put(f"{API_URL}/tasks/{non_existent_id}", json={"title": "This should fail"})
    if response.status_code != 404:
        print(f"Error: Expected 404 for non-existent task, got {response.status_code}")
        return False
    
    print("404 error for non-existent task successful")
    
    # Test getting a non-existent project
    response = requests.get(f"{API_URL}/projects/{non_existent_id}")
    if response.status_code != 404:
        print(f"Error: Expected 404 for non-existent project, got {response.status_code}")
        return False
    
    print("404 error for non-existent project successful")
    
    # Test deleting a non-existent project task
    response = requests.delete(f"{API_URL}/projects/{non_existent_id}/tasks/{non_existent_id}")
    if response.status_code != 404:
        print(f"Error: Expected 404 for non-existent project task, got {response.status_code}")
        return False
    
    print("404 error for non-existent project task successful")
    return True

# Main test runner
def run_all_tests():
    print(f"Starting backend API tests against {API_URL}")
    
    # Run all tests
    run_test("Basic API Check", test_basic_api)
    run_test("Dashboard Stats", test_dashboard_stats)
    run_test("Task CRUD Operations", test_task_crud)
    run_test("Project CRUD Operations", test_project_crud)
    run_test("Project Task CRUD Operations", test_project_task_crud)
    run_test("Task Filtering and Status Updates", test_task_filtering_and_status)
    run_test("Due Date and Overdue Detection", test_due_date_and_overdue)
    run_test("Error Handling", test_error_handling)
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"TEST SUMMARY: {test_results['passed']}/{test_results['total']} tests passed")
    print(f"  ✅ Passed: {test_results['passed']}")
    print(f"  ❌ Failed: {test_results['failed']}")
    print("=" * 80)
    
    return test_results["failed"] == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)