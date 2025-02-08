class ServerConfig:
    HOST: str = "0.0.0.0"  # Changed from localhost to allow external connections
    PORT: int = 8765
    DEBUG: bool = True
    SSL_ENABLED: bool = False  # Set to False for initial testing