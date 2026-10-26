function createCourseModel(db) {
    return {
        findActive(id) {
            return db.get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [id]);
        },

        /** Cursos com matrículas, alunos e pagamentos numa única consulta (sem N+1). */
        listWithEnrollments() {
            return db.all(`
                SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
                       u.name AS student, p.amount, p.status
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id
                LEFT JOIN users u ON u.id = e.user_id
                LEFT JOIN payments p ON p.enrollment_id = e.id
                ORDER BY c.id, e.id
            `);
        },
    };
}

module.exports = { createCourseModel };
