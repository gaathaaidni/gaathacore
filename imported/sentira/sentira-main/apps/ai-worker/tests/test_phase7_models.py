import importlib.util
from pathlib import Path

def load_models():
    path = Path(__file__).resolve().parents[1] / "models.py"
    spec = importlib.util.spec_from_file_location("sentira_ai_models", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

models = load_models()

def test_model_registry_and_metadata():
    provider = models.ConfigurableModelProvider(models.ModelConfig(name="custom", version="2", task="segmentation", device="cpu", confidence_threshold=0.7, image_size=512))
    registry = models.ModelRegistry()
    registry.register("seg", provider)
    meta = registry.get("seg").metadata()
    assert meta.name == "custom"
    assert meta.task == "segmentation"
    assert meta.confidence_threshold == 0.7

def test_camera_specific_model_override():
    cfg = models.ModelConfig(name="base", camera_overrides={"cam-a": {"name": "edge", "frame_rate": 3.0}})
    provider = models.ConfigurableModelProvider(cfg)
    provider.predict(None, camera_id="cam-a")
    assert provider.metadata().name == "edge"
