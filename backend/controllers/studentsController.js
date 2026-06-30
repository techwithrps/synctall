const Student = require('../models/student');
const SyncJob = require('../models/syncJob');

class StudentsController {
  /**
   * Retrieves a paginated and filterable list of students
   */
  static async getStudents(req, res) {
    try {
      const page = parseInt(req.query.page) || 1;
      const size = parseInt(req.query.size) || 20;
      const { course, semester, session, status } = req.query;

      const result = await Student.findAll({ page, size, course, semester, session, status });
      res.json(result);
    } catch (err) {
      console.error('Error in getStudents controller:', err.message);
      res.status(500).json({ error: err.message });
    }
  }

  /**
   * Performs multi-field search across Name, Enrollment No, and Roll No
   */
  static async searchStudents(req, res) {
    try {
      const q = req.query.q;
      if (!q || q.length < 2) {
        return res.status(400).json({ error: 'Search query must be at least 2 characters' });
      }

      const results = await Student.search(q);
      res.json(results);
    } catch (err) {
      console.error('Error in searchStudents controller:', err.message);
      res.status(500).json({ error: err.message });
    }
  }

  /**
   * Retrieves specific student details by id (UUID or Enrollment No)
   */
  static async getStudentById(req, res) {
    try {
      const student = await Student.findById(req.params.id);
      if (!student) {
        return res.status(404).json({ error: 'Student record not found in system' });
      }
      res.json(student);
    } catch (err) {
      console.error('Error in getStudentById controller:', err.message);
      res.status(500).json({ error: err.message });
    }
  }

  /**
   * Computes aggregated stats for dashboard reporting
   */
  static async getDashboardStats(req, res) {
    try {
      // 1. Run parallel DB counts
      const [totalStudents, activeStudents, inactiveStudents, recentSyncJobs, distributionData] = await Promise.all([
        Student.getCount(),
        Student.getCount({ status: 'Active' }),
        Student.getCount({ status: 'Inactive' }),
        SyncJob.findRecent(6),
        Student.getDistributionData()
      ]);

      const lastSyncJob = recentSyncJobs.length > 0 ? recentSyncJobs[0] : null;

      // 2. Perform in-memory groupings
      const courseWiseDistribution = {};
      const genderWiseDistribution = {};

      distributionData.forEach(student => {
        if (student.course) {
          courseWiseDistribution[student.course] = (courseWiseDistribution[student.course] || 0) + 1;
        }
        if (student.gender) {
          genderWiseDistribution[student.gender] = (genderWiseDistribution[student.gender] || 0) + 1;
        }
      });

      res.json({
        total_students: totalStudents,
        active_students: activeStudents,
        inactive_students: inactiveStudents,
        last_sync_job: lastSyncJob,
        recent_sync_jobs: recentSyncJobs,
        course_wise_distribution: courseWiseDistribution,
        gender_wise_distribution: genderWiseDistribution
      });
    } catch (err) {
      console.error('Error in getDashboardStats controller:', err.message);
      res.status(500).json({ error: err.message });
    }
  }
}

module.exports = StudentsController;
