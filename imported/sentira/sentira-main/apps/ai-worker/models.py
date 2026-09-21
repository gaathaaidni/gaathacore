from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
import os, time

@dataclass
class ModelConfig:
    task: str = "detection"
    name: str = "lightweight"
    version: str = "1.0"
    confidence_threshold: float = 0.5
    device: str = "cpu"
    frame_rate: float = 5.0
    image_size: int = 640
    classes: List[str] = field(default_factory=lambda: ["person", "vehicle", "animal", "object"])
    camera_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)

@dataclass
class ModelMetadata:
    name: str
    version: str
    task: str
    classes: List[str]
    device: str
    input_size: int
    confidence_threshold: float
    processing_time_ms: float = 0.0

class ModelProvider(Protocol):
    def metadata(self) -> ModelMetadata: ...
    def predict(self, frame: Any, camera_id: Optional[str] = None) -> List[Dict[str, Any]]: ...

class ConfigurableModelProvider:
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig(
            task=os.getenv("AI_MODEL_TASK", "detection"),
            name=os.getenv("AI_MODEL_NAME", "lightweight"),
            version=os.getenv("AI_MODEL_VERSION", "1.0"),
            confidence_threshold=float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.5")),
            device=os.getenv("AI_DEVICE", "cpu"),
            frame_rate=float(os.getenv("AI_FPS", "5")),
            image_size=int(os.getenv("AI_IMAGE_SIZE", "640")),
        )
        self._last_ms = 0.0

    def camera_config(self, camera_id: Optional[str]) -> ModelConfig:
        if camera_id and camera_id in self.config.camera_overrides:
            data = {**self.config.__dict__, **self.config.camera_overrides[camera_id]}
            return ModelConfig(**{k: v for k, v in data.items() if k in ModelConfig.__dataclass_fields__})
        return self.config

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(self.config.name, self.config.version, self.config.task, self.config.classes, self.config.device, self.config.image_size, self.config.confidence_threshold, self._last_ms)

    def predict(self, frame: Any, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        start = time.perf_counter()
        cfg = self.camera_config(camera_id)
        # Adapter point for YOLO/ONNX/TensorRT/custom providers. The base provider never fabricates detections.
        self._last_ms = (time.perf_counter() - start) * 1000
        self.config = cfg
        return []

DetectionProvider = ConfigurableModelProvider
ClassificationProvider = ConfigurableModelProvider
SegmentationProvider = ConfigurableModelProvider
PoseProvider = ConfigurableModelProvider
CustomModelProvider = ConfigurableModelProvider

class ModelRegistry:
    def __init__(self):
        self._providers: Dict[str, ModelProvider] = {}
    def register(self, key: str, provider: ModelProvider) -> None:
        self._providers[key] = provider
    def get(self, key: str) -> ModelProvider:
        if key not in self._providers:
            raise KeyError(f"model provider not registered: {key}")
        return self._providers[key]
    def list_metadata(self) -> List[ModelMetadata]:
        return [p.metadata() for p in self._providers.values()]

# Backward-compatible alias used by earlier phases.
YoloModelProvider = ConfigurableModelProvider
