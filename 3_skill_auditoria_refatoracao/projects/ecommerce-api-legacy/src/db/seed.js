const crypto = require('crypto');
const { hashPassword } = require('../services/passwordHasher');

async function seed(db, { seedUserPassword }) {
    const { total } = await db.get('SELECT COUNT(*) AS total FROM courses');
    if (total > 0) return;

    // Sem SEED_USER_PASSWORD a conta demo recebe senha aleatória não divulgada.
    const password = seedUserPassword || crypto.randomBytes(16).toString('hex');
    await db.transaction(async (tx) => {
        await tx.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', hashPassword(password)]);
        await tx.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)', ['Clean Architecture', 997.0, 'Docker', 497.0]);
        await tx.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await tx.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
    });
}

module.exports = { seed };
