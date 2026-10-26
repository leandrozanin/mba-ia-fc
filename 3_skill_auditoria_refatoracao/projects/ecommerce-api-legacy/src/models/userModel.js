function createUserModel(db) {
    return {
        findActiveByEmail(email) {
            return db.get('SELECT id, name, email, pass FROM users WHERE email = ? AND deleted_at IS NULL', [email]);
        },

        async create(tx, { name, email, passwordHash }) {
            const { lastID } = await tx.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
            return lastID;
        },

        /** Remove dados pessoais mantendo o histórico financeiro íntegro. */
        async anonymize(tx, id) {
            const { changes } = await tx.run(
                "UPDATE users SET name = NULL, email = NULL, pass = NULL, deleted_at = datetime('now') WHERE id = ? AND deleted_at IS NULL",
                [id]
            );
            return changes > 0;
        },
    };
}

module.exports = { createUserModel };
