const express = require('express');
const cors = require('cors');
const config = require('./config');
const StudentsController = require('./controllers/studentsController');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Routes Mounts
const studentsRouter = require('./routes/students');
const syncRouter = require('./routes/sync');

app.use('/api/v1/students', studentsRouter);
app.use('/api/v1/sync', syncRouter);

// Dashboard stats endpoint (Routed to MVC StudentsController)
app.get('/api/v1/dashboard/stats', StudentsController.getDashboardStats);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'Tally College Integration MVC Node.js Express API',
    timestamp: new Date().toISOString()
  });
});

// Root endpoint welcome
app.get('/', (req, res) => {
  res.json({
    message: 'Welcome to the Tally College Integration Node.js MVC REST API Service.',
    docs: 'Refer to README for api definitions.'
  });
});

// Boot the server
app.listen(config.port, () => {
  console.log(`=======================================================`);
  console.log(`Tally Integration Node.js MVC server running on port: ${config.port}`);
  console.log(`Database Connection Endpoint: ${config.supabaseUrl}`);
  console.log(`=======================================================`);
});
