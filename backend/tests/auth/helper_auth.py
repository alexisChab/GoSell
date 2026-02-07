def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})

def logout_access(client, csrf=None):
    headers = {}
    if csrf:
        headers["X-CSRF-TOKEN"] = csrf
    return client.post("/api/auth/logout", json={}, headers=headers)

def me(client):
    return client.get("/api/auth/me")
