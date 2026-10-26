const sqlite3 = require('sqlite3');

const SCHEMA = [
    'PRAGMA foreign_keys = ON',
    'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pass TEXT, deleted_at DATETIME)',
    'CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)',
    `CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        course_id INTEGER REFERENCES courses(id),
        UNIQUE (user_id, course_id)
    )`,
    'CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER REFERENCES enrollments(id), amount REAL, status TEXT)',
    'CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)',
];

/** Wrapper com Promises sobre o driver de callbacks do sqlite3. */
class Database {
    constructor(filename) {
        this.conn = new sqlite3.Database(filename);
        this.queue = Promise.resolve();
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.conn.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.conn.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.conn.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    /**
     * Executa `work` dentro de BEGIN/COMMIT, com ROLLBACK em erro. Transações são
     * enfileiradas porque a conexão é única.
     */
    transaction(work) {
        const result = this.queue.then(async () => {
            await this.run('BEGIN IMMEDIATE');
            try {
                const value = await work(this);
                await this.run('COMMIT');
                return value;
            } catch (err) {
                await this.run('ROLLBACK');
                throw err;
            }
        });
        this.queue = result.catch(() => {});
        return result;
    }

    async migrate() {
        for (const ddl of SCHEMA) await this.run(ddl);
    }

    close() {
        return new Promise((resolve, reject) => this.conn.close((err) => (err ? reject(err) : resolve())));
    }
}

module.exports = { Database };
