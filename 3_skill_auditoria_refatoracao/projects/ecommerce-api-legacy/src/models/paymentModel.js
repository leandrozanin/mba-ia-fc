const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

function create(db, { enrollmentId, amount, status }) {
    return db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrollmentId, amount, status]);
}

module.exports = { PAYMENT_STATUS, create };
