from backend.astraos.training import AdaptiveTrainingPipeline
import tempfile
import os
from pathlib import Path


def sample_history(count=20):
    history = []
    for i in range(count):
        history.append({
            "timestamp": float(i),
            "cpu": {"usage_percent": 50.0 + i * 2},
            "memory": {"percent": 60.0 + i},
            "swap": {"percent": 10.0},
            "thermal": {"hottest_c": 45.0 + i * 0.5},
            "network": {"bytes_recv_per_sec": 1000.0 * i},
            "disk": {"read_bytes_per_sec": 500.0 * i, "write_bytes_per_sec": 300.0 * i},
        })
    return history


def test_training_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        assert pipeline.model_dir.exists()


def test_training_insufficient_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        history = sample_history(5)  # Less than required 12 samples
        result = pipeline.train(history)
        
        assert result["status"] == "insufficient_data"
        assert result["sample_count"] == 5


def test_training_successful():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        history = sample_history(20)
        result = pipeline.train(history)
        
        assert result["status"] == "trained"
        assert "artifact" in result
        assert "model_path" in result
        assert "metadata_path" in result


def test_training_artifact_structure():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        history = sample_history(20)
        result = pipeline.train(history)
        
        artifact = result["artifact"]
        assert "version" in artifact
        assert "created_at" in artifact
        assert "sample_count" in artifact
        assert "features" in artifact
        assert "cluster_counts" in artifact


def test_training_features():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        history = sample_history(20)
        result = pipeline.train(history)
        
        artifact = result["artifact"]
        expected_features = ["cpu", "memory", "swap", "temperature", "network_rx_kbps", "disk_kbps"]
        assert artifact["features"] == expected_features


def test_training_model_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        history = sample_history(20)
        result = pipeline.train(history)
        
        # Check that model file was created
        model_path = Path(result["model_path"])
        assert model_path.exists()
        
        # Check that metadata file was created
        metadata_path = Path(result["metadata_path"])
        assert metadata_path.exists()


def test_training_versions():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        history = sample_history(20)
        
        # Train multiple models with delay to ensure different timestamps
        pipeline.train(history)
        import time
        time.sleep(1.0)
        pipeline.train(history)
        
        versions = pipeline.versions()
        assert len(versions) == 2
        assert all("version" in v for v in versions)


def test_training_version_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        history = sample_history(20)
        result = pipeline.train(history)
        
        artifact = result["artifact"]
        version = artifact["version"]
        # Version should be in YYYYMMDD-HHMMSS format (15 characters)
        assert len(version) == 15  # "20240101-120000" format
        assert "-" in version


def test_training_cluster_counts():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        history = sample_history(20)
        result = pipeline.train(history)
        
        artifact = result["artifact"]
        cluster_counts = artifact["cluster_counts"]
        assert isinstance(cluster_counts, dict)
        assert len(cluster_counts) > 0


def test_training_features_extraction():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        history = sample_history(20)
        
        # Test feature extraction
        features = pipeline._features(history[0])
        assert isinstance(features, list)
        assert len(features) == 6  # 6 features
        assert all(isinstance(f, (int, float)) for f in features)


def test_training_features_with_missing_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = AdaptiveTrainingPipeline(tmpdir)
        
        # Test with missing cpu data
        item = {
            "timestamp": 1.0,
            "memory": {"percent": 60.0},
            "swap": {"percent": 10.0},
            "thermal": {"hottest_c": 45.0},
            "network": {"bytes_recv_per_sec": 1000.0},
            "disk": {"read_bytes_per_sec": 500.0, "write_bytes_per_sec": 300.0},
        }
        features = pipeline._features(item)
        assert features is None
