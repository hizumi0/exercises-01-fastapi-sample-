from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sql_app.main import app, get_db
from sql_app.database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_user():
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "id" in data
    assert "is_active" in data
    assert "api_token" in data
    return data["api_token"]

def test_read_users():
    api_token = test_create_user()
    response = client.get("/users/", headers={"X-API-TOKEN": api_token})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_user():
    api_token = test_create_user()
    response = client.get("/users/1", headers={"X-API-TOKEN": api_token})
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_create_item():
    api_token = test_create_user()
    response = client.post(
        "/users/1/items/",
        headers={"X-API-TOKEN": api_token},
        json={"title": "Test Item", "description": "This is a test item"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test Item"

def test_read_items():
    api_token = test_create_user()
    response = client.get("/items/", headers={"X-API-TOKEN": api_token})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_health_check():
    response = client.get("/health-check")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_unauthorized_access():
    response = client.get("/users/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API token"

def test_read_own_items():
    api_token = test_create_user()
    # まずアイテムを作成
    client.post(
        "/users/1/items/",
        headers={"X-API-TOKEN": api_token},
        json={"title": "My Item", "description": "This is my item"},
    )
    # 自分のアイテムを取得
    response = client.get("/me/items/", headers={"X-API-TOKEN": api_token})
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) > 0
    assert items[0]["title"] == "My Item"

def test_delete_user():
    # 2人のユーザーを作成
    api_token1 = test_create_user()
    response = client.post(
        "/users/",
        json={"email": "test2@example.com", "password": "testpassword2"},
    )
    api_token2 = response.json()["api_token"]
    
    # 最初のユーザーにアイテムを追加
    client.post(
        "/users/1/items/",
        headers={"X-API-TOKEN": api_token1},
        json={"title": "Test Item", "description": "This is a test item"},
    )
    
    # 最初のユーザーを削除
    response = client.delete("/users/1", headers={"X-API-TOKEN": api_token2})
    assert response.status_code == 200
    assert response.json()["is_active"] == False
    
    # 削除されたユーザーのアイテムが2番目のユーザーに移されたことを確認
    response = client.get("/me/items/", headers={"X-API-TOKEN": api_token2})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["title"] == "Test Item"