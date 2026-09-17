"""Todo tests."""

import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str = "todo@example.com") -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_todo(client: AsyncClient):
    """Test creating a new todo."""
    token = await get_auth_token(client, "create@example.com")

    response = await client.post(
        "/api/v1/todos",
        json={"title": "Test Todo", "description": "A test todo item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "A test todo item"
    assert data["completed"] is False


@pytest.mark.asyncio
async def test_get_todos(client: AsyncClient):
    """Test getting todo list."""
    token = await get_auth_token(client, "list@example.com")

    # Create a todo first
    await client.post(
        "/api/v1/todos",
        json={"title": "List Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get todos
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_update_todo(client: AsyncClient):
    """Test updating a todo."""
    token = await get_auth_token(client, "update@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Update Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Update it
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title", "completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_todo(client: AsyncClient):
    """Test deleting a todo."""
    token = await get_auth_token(client, "delete@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Delete Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_single_todo(client: AsyncClient):
    """Test getting a single todo by ID."""
    token = await get_auth_token(client, "single@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Single Todo", "description": "Get me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Get it
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Single Todo"


@pytest.mark.asyncio
async def test_cannot_get_other_users_todo(client: AsyncClient):
    """User B không thể GET todo của User A — trả về 404."""
    token_a = await get_auth_token(client, "idor-a@example.com")
    token_b = await get_auth_token(client, "idor-b@example.com")

    # User A tạo 1 todo
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "A's secret todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_resp.json()["id"]

    # User B cố GET todo của A
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_update_other_users_todo(client: AsyncClient):
    """User B không thể PUT todo của User A — trả về 404, title không bị đổi."""
    token_a = await get_auth_token(client, "idor-update-a@example.com")
    token_b = await get_auth_token(client, "idor-update-b@example.com")

    original_title = "A's original title"
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": original_title},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_resp.json()["id"]

    # User B cố PUT todo của A
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404

    # Xác nhận title của A vẫn không đổi
    verify_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["title"] == original_title


@pytest.mark.asyncio
async def test_cannot_delete_other_users_todo(client: AsyncClient):
    """User B không thể DELETE todo của User A — trả về 404, todo vẫn còn tồn tại."""
    token_a = await get_auth_token(client, "idor-delete-a@example.com")
    token_b = await get_auth_token(client, "idor-delete-b@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Don't delete me"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_resp.json()["id"]

    # User B cố DELETE todo của A
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404

    # Xác nhận todo của A vẫn còn tồn tại
    verify_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert verify_resp.status_code == 200
