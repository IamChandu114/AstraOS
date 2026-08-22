from backend.astraos.containers import ContainerAwareness


def test_container_awareness_initialization():
    awareness = ContainerAwareness()
    assert awareness._cache is None
    assert awareness._cache_at == 0.0


def test_container_inspect():
    awareness = ContainerAwareness()
    result = awareness.inspect()
    
    assert "timestamp" in result
    assert "docker" in result
    assert "kubernetes" in result
    assert "containerized" in result
    assert "cached" in result


def test_container_docker_structure():
    awareness = ContainerAwareness()
    result = awareness.inspect()
    
    docker = result["docker"]
    assert "available" in docker
    assert "containers" in docker
    assert isinstance(docker["containers"], list)


def test_container_kubernetes_structure():
    awareness = ContainerAwareness()
    result = awareness.inspect()
    
    kubernetes = result["kubernetes"]
    assert "available" in kubernetes
    assert "pods" in kubernetes
    assert isinstance(kubernetes["pods"], list)


def test_container_caching():
    awareness = ContainerAwareness()
    
    # First call
    result1 = awareness.inspect()
    assert result1["cached"] == False
    
    # Second call should use cache
    result2 = awareness.inspect()
    assert result2["cached"] == True
    assert "cache_age_seconds" in result2


def test_container_containerized_flag():
    awareness = ContainerAwareness()
    result = awareness.inspect()
    
    containerized = result["containerized"]
    assert isinstance(containerized, bool)


def test_container_docker_unavailable():
    awareness = ContainerAwareness()
    result = awareness.inspect()
    
    docker = result["docker"]
    # If Docker is not available, should still return valid structure
    if not docker["available"]:
        assert docker["containers"] == []
        assert "error" in docker or docker["available"] == False


def test_container_kubernetes_unavailable():
    awareness = ContainerAwareness()
    result = awareness.inspect()
    
    kubernetes = result["kubernetes"]
    # If Kubernetes is not available, should still return valid structure
    if not kubernetes["available"]:
        assert kubernetes["pods"] == []
        assert "error" in kubernetes or kubernetes["available"] == False
