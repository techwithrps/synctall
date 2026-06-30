const express = require('express');
const router = express.Router();
const StudentsController = require('../controllers/studentsController');

// GET /api/v1/students - Paginated and filterable students list
router.get('/', StudentsController.getStudents);

// GET /api/v1/students/search - Multi-field search
router.get('/search', StudentsController.searchStudents);

// GET /api/v1/students/:id - Fetch single student details
router.get('/:id', StudentsController.getStudentById);

module.exports = router;
