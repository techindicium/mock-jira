FROM python:3.12-slim

WORKDIR /app

COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements-mcp.txt

COPY mcp_server/ ./mcp_server/

ENV PORT=8001
ENV API_BASE_URL=http://issue-tracker-api:8000

EXPOSE 8001

CMD ["python3", "-m", "mcp_server.server"]
