const supabase = require('../db');

class SyncJob {
  /**
   * Fetch recent sync jobs
   */
  static async findRecent(limit = 10) {
    const { data, error } = await supabase
      .from('sync_jobs')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(limit);

    if (error) throw error;
    return data || [];
  }

  /**
   * Find any active sync jobs (RUNNING or PENDING)
   */
  static async findActive() {
    const { data, error } = await supabase
      .from('sync_jobs')
      .select('*')
      .in('status', ['RUNNING', 'PENDING']);

    if (error) throw error;
    return data || [];
  }

  /**
   * Queue a new pending sync job
   */
  static async createPending() {
    const payload = {
      status: 'PENDING',
      started_at: new Date().toISOString(),
      total_records: 0,
      processed_records: 0,
      failed_records: 0
    };

    const { data, error } = await supabase
      .from('sync_jobs')
      .insert(payload)
      .select();

    if (error) throw error;
    return data && data.length > 0 ? data[0] : null;
  }
}

module.exports = SyncJob;
