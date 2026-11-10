const path = require('path')

module.exports = {
  apps: [
    {
      name: 'backend',
      script: path.join(__dirname, '.venv/bin/uvicorn'),
      args: 'FastAPI_2:app --host 127.0.0.1 --port 8000',
      interpreter: 'none',
      cwd: __dirname,
    },
    {
      name: 'frontend',
      script: path.join(__dirname, 'marktplaats-frontend/.output/server/index.mjs'),
      cwd: path.join(__dirname, 'marktplaats-frontend'),
      env: {
        PORT: 3000,
        HOST: '127.0.0.1',
      },
    },
  ],
}
