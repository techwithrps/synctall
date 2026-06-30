const SyncJob = require('../models/syncJob');

class SyncController {
  /**
   * Retrieves synchronization job history details
   */
  static async getSyncStatus(req, res) {
    try {
      const limit = parseInt(req.query.limit) || 10;
      const history = await SyncJob.findRecent(limit);
      res.json(history);
    } catch (err) {
      console.error('Error in getSyncStatus controller:', err.message);
      res.status(500).json({ error: err.message });
    }
  }

  /**
   * Triggers a remote queued sync operation
   */
  static async triggerSyncRun(req, res) {
    try {
      // Prevent overlapping concurrent loops
      const activeJobs = await SyncJob.findActive();
      if (activeJobs && activeJobs.length > 0) {
        return res.json({
          message: 'A synchronization process is already pending or active.',
          sync_job_id: activeJobs[0].id,
          status: activeJobs[0].status
        });
      }

      // Add a PENDING task
      const queuedJob = await SyncJob.createPending();
      if (!queuedJob) {
        throw new Error('Database failed to insert pending queue record.');
      }

      res.json({
        message: 'Synchronization job successfully queued.',
        sync_job_id: queuedJob.id,
        status: queuedJob.status
      });
    } catch (err) {
      console.error('Error in triggerSyncRun controller:', err.message);
      res.status(500).json({ error: err.message });
    }
  }
}

module.exports = SyncController;
