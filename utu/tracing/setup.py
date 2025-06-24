from phoenix.otel import register, TracerProvider

def setup_phoenix_tracing() -> TracerProvider:
    """ 
    TODO: add try-except
    """
    tracer_provider = register(
        endpoint="http://9.134.230.111:4317",
        project_name="uTu agent",
        batch=True,
        # protocol="grpc", # grpc | http/protobuf, will automatically inferred!
        auto_instrument=True,# Auto-instrument your app based on installed OI dependencies
    )
    return tracer_provider
