def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_full_user_flow(client):
    # Register first user
    phone1 = "13800000001"
    response = client.post("/api/v1/auth/request-code", json={"phone": phone1})
    assert response.status_code == 200
    code1 = response.json()["code"]

    response = client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone1,
            "code": code1,
            "wechat_id": "wechat001",
        },
    )
    assert response.status_code == 200
    token1 = response.json()["access_token"]

    profile_resp = client.get("/api/v1/users/me", headers=auth_headers(token1))
    assert profile_resp.status_code == 200
    profile1 = profile_resp.json()
    assert profile1["points"] == 100
    invite_code = profile1["invite_code"]
    assert invite_code

    post_payload = {
        "title": "出售iPhone15",
        "keywords": "iPhone15,出售,手机",
        "price": 5800,
        "trade_type": 2,
    }
    post_resp = client.post("/api/v1/posts", json=post_payload, headers=auth_headers(token1))
    assert post_resp.status_code == 201
    post_id = post_resp.json()["id"]

    balance_resp = client.get("/api/v1/points/balance", headers=auth_headers(token1))
    assert balance_resp.json()["points"] == 90

    # Register second user with invite code
    phone2 = "13800000002"
    response = client.post("/api/v1/auth/request-code", json={"phone": phone2})
    assert response.status_code == 200
    code2 = response.json()["code"]

    response = client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone2,
            "code": code2,
            "wechat_id": "wechat002",
            "invite_code": invite_code,
        },
    )
    assert response.status_code == 200
    token2 = response.json()["access_token"]

    # Invite rewards should trigger after first post
    post_payload2 = {
        "title": "求购MacBook",
        "keywords": "MacBook,求购,电脑",
        "price": 9000,
        "trade_type": 1,
    }
    post_resp2 = client.post("/api/v1/posts", json=post_payload2, headers=auth_headers(token2))
    assert post_resp2.status_code == 201

    balance_user2 = client.get("/api/v1/points/balance", headers=auth_headers(token2)).json()["points"]
    assert balance_user2 == 120

    balance_user1 = client.get("/api/v1/points/balance", headers=auth_headers(token1)).json()["points"]
    assert balance_user1 == 100

    # User2 views contact of user1's post
    view_resp = client.post(f"/api/v1/posts/{post_id}/contact", headers=auth_headers(token2))
    assert view_resp.status_code == 200
    contact_id = view_resp.json()["id"]

    balance_after_view = client.get("/api/v1/points/balance", headers=auth_headers(token2)).json()["points"]
    assert balance_after_view == 119

    # Second view should not deduct additional points
    second_view = client.post(f"/api/v1/posts/{post_id}/contact", headers=auth_headers(token2))
    assert second_view.status_code == 200
    assert second_view.json()["id"] == contact_id
    assert client.get("/api/v1/points/balance", headers=auth_headers(token2)).json()["points"] == 119

    # Confirm deal and ensure stats update
    confirm_resp = client.post(
        f"/api/v1/posts/{post_id}/contact/{contact_id}/confirm",
        json={"is_deal": True},
        headers=auth_headers(token2),
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["is_deal"] is True

    owner_profile = client.get("/api/v1/users/me", headers=auth_headers(token1)).json()
    assert owner_profile["total_deals"] == 1
    assert owner_profile["deal_rate"] == 100.0

    # Listing endpoint should return at least one post
    list_resp = client.get("/api/v1/posts")
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["total"] >= 1
    assert any(item["id"] == post_id for item in payload["items"])
