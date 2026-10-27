const { hashPassword } = require('../services/passwordHasher');
const { PAYMENT_STATUS } = require('../models/paymentModel');

const SCHEMA = `
    PRAGMA foreign_keys = ON;
    CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
    CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
    CREATE TABLE enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id)
    );
    CREATE TABLE payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL,
        status TEXT
    );
    CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

async function initSchema(db) {
    await db.exec(SCHEMA);
}

async function seed(db) {
    await db.transaction(async (tx) => {
        const seedPassword = await hashPassword('123');
        await tx.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", ['Leonan', 'leonan@fullcycle.com.br', seedPassword]);
        await tx.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
        await tx.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
        await tx.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)", [PAYMENT_STATUS.PAID]);
    });
}

module.exports = { initSchema, seed };
