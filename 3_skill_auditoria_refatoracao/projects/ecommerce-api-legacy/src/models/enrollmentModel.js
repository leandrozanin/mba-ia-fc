function createEnrollmentModel(db) {
    return {
        async exists(userId, courseId) {
            const row = await db.get('SELECT 1 FROM enrollments WHERE user_id = ? AND course_id = ?', [userId, courseId]);
            return Boolean(row);
        },

        async create(tx, { userId, courseId }) {
            const { lastID } = await tx.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
            return lastID;
        },

        async recordPayment(tx, { enrollmentId, amount, status }) {
            await tx.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, amount, status]);
        },

        async audit(tx, action) {
            await tx.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
        },
    };
}

module.exports = { createEnrollmentModel };
