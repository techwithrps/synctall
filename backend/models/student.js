const supabase = require('../db');

class Student {
  /**
   * Fetch a paginated and filtered list of students
   */
  static async findAll({ page = 1, size = 20, course, semester, session, status }) {
    const start = (page - 1) * size;
    const end = start + size - 1;

    let query = supabase
      .from('students')
      .select('*', { count: 'exact' });

    if (course) query = query.eq('course', course);
    if (semester) query = query.eq('semester', semester);
    if (session) query = query.eq('session', session);
    if (status) query = query.eq('status', status);

    const { data, count, error } = await query
      .order('student_name', { ascending: true })
      .range(start, end);

    if (error) throw error;

    return {
      items: data || [],
      total: count || 0,
      page,
      size,
      pages: Math.ceil((count || 0) / size)
    };
  }

  /**
   * Perform multi-field search
   */
  static async search(q) {
    const orFilter = `student_name.ilike.%${q}%,enrollment_no.ilike.%${q}%,roll_no.ilike.%${q}%`;
    const { data, error } = await supabase
      .from('students')
      .select('*')
      .or(orFilter)
      .limit(50);

    if (error) throw error;
    return data || [];
  }

  /**
   * Find a single student by UUID or Enrollment Number
   */
  static async findById(id) {
    let query = supabase.from('students').select('*');

    if (id.length === 36 && id.split('-').length === 5) {
      query = query.eq('id', id);
    } else {
      query = query.eq('enrollment_no', id);
    }

    const { data, error } = await query;
    if (error) throw error;
    
    return data && data.length > 0 ? data[0] : null;
  }

  /**
   * Aggregate student distribution counts
   */
  static async getDistributionData() {
    const { data, error } = await supabase
      .from('students')
      .select('course, gender');

    if (error) throw error;
    return data || [];
  }

  /**
   * Get exact row counts based on filters
   */
  static async getCount(filters = {}) {
    let query = supabase.from('students').select('id', { count: 'exact', head: true });
    
    if (filters.status) {
      query = query.eq('status', filters.status);
    }
    
    const { count, error } = await query;
    if (error) throw error;
    return count || 0;
  }
}

module.exports = Student;
