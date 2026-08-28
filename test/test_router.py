from microfw.router import RadixRouter

def test_radix_router_exact_match():
    router = RadixRouter()
    
    handler = {"name": "index"}
    router.add_route("GET", "/", handler)
    router.add_route("GET", "/about", {"name": "about"})
    
    match, kwargs = router.match_route("GET", "/")
    assert match == handler
    assert kwargs == {}

    match, kwargs = router.match_route("GET", "/about")
    assert match == {"name": "about"}
    assert kwargs == {}

def test_radix_router_dynamic_match():
    router = RadixRouter()
    
    handler = {"name": "get_user"}
    router.add_route("GET", "/users/{id}", handler)
    router.add_route("GET", "/users/{id}/profile", {"name": "user_profile"})
    
    match, kwargs = router.match_route("GET", "/users/123")
    assert match == handler
    assert kwargs == {"id": "123"}
    
    match, kwargs = router.match_route("GET", "/users/123/profile")
    assert match == {"name": "user_profile"}
    assert kwargs == {"id": "123"}

def test_radix_router_not_found():
    router = RadixRouter()
    router.add_route("GET", "/users/{id}", {"name": "get_user"})
    
    match, kwargs = router.match_route("GET", "/users")
    assert match is None
    
    match, kwargs = router.match_route("POST", "/users/123")
    assert match is None

if __name__ == "__main__":
    test_radix_router_exact_match()
    test_radix_router_dynamic_match()
    test_radix_router_not_found()
    print("All RadixRouter tests passed!")
