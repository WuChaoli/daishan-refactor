from rag_stream.main import app
from rag_stream.config.settings import settings


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.server.host, port=settings.server.port)
