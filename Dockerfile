FROM python:3.12-slim

# Official Node 20 copied in (more reliable than apt's nodejs/npm)
COPY --from=node:20-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

ENV PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /app

COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY frontend/package*.json frontend/
RUN cd frontend && npm install

COPY backend/ backend/
COPY frontend/ frontend/

EXPOSE 5000 5173

CMD ["sh", "-c", "cd /app/backend && gunicorn -b 0.0.0.0:5000 --workers 1 --threads 4 --timeout 120 app:app & cd /app/frontend && npm run dev -- --host 0.0.0.0"]