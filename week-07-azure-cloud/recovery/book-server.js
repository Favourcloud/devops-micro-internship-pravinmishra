const express = require('express');
const initializeDatabase = require('./config/db');

async function start() {
  const sequelize = await initializeDatabase();
  const app = express();
  app.disable('x-powered-by');
  app.use(express.json({ limit: '32kb' }));
  app.get('/health', async (_req, res) => {
    try { await sequelize.query('SELECT 1'); res.json({status:'ok', database:'connected'}); }
    catch { res.status(503).json({status:'unavailable'}); }
  });
  app.use('/api/users', require('./routes/userRoutes')(sequelize));
  app.use('/api/books', require('./routes/bookRoutes')(sequelize));
  app.use('/api/reviews', require('./routes/reviewRoutes')(sequelize));
  app.use((_err, _req, res, _next) => res.status(500).json({message:'Request failed'}));
  const server=app.listen(5000, '0.0.0.0', () => console.log('Book Review API listening on private port 5000'));
  process.on('SIGTERM', () => server.close(() => sequelize.close().then(() => process.exit(0))));
}
start().catch(() => { console.error('Backend startup failed'); process.exit(1); });
