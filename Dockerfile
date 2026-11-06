FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    OMP_NUM_THREADS=2 \
    OPENBLAS_NUM_THREADS=2 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

WORKDIR /app

COPY job_market/ ./
COPY docker/ /opt/demo/

RUN python -m pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 app \
    && chown -R app:app /app

USER app

RUN python /opt/demo/check_demo.py

EXPOSE 8502

ENTRYPOINT ["/bin/sh", "/opt/demo/entrypoint.sh"]
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8502"]
