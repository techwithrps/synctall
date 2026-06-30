const express = require('express');
const router = express.Router();
const SyncController = require('../controllers/syncController');

// GET /api/v1/sync/status - Fetch recent sync job history records
router.get('/status', SyncController.getSyncStatus);

// POST /api/v1/sync/run - Queue a new sync run
router.post('/run', SyncController.triggerSyncRun);

module.exports = router;
