function findActiveById(db, id) {
    return db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [id]);
}

// Uma única consulta para o relatório financeiro (evita N+1).
function listWithEnrollmentsAndPayments(db) {
    return db.all(`
        SELECT c.id AS course_id, c.title AS course_title,
               e.id AS enrollment_id, u.name AS user_name,
               p.amount AS payment_amount, p.status AS payment_status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN payments p ON p.enrollment_id = e.id
        ORDER BY c.id, e.id, p.id
    `);
}

module.exports = { findActiveById, listWithEnrollmentsAndPayments };
