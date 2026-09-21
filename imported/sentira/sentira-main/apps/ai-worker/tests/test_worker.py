from models import ConfigurableModelProvider

def test_model_metadata_is_available_without_gpu():
    metadata = ConfigurableModelProvider().metadata()
    assert metadata.device == 'cpu'
