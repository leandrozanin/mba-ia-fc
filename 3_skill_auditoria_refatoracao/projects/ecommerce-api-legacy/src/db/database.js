const sqlite3 = require('sqlite3');

// Wrapper com Promises sobre uma única conexão sqlite3.
// As transações são enfileiradas: a conexão é compartilhada, então duas
// transações concorrentes não podem ficar abertas ao mesmo tempo.
class Database {
    constructor(connection) {
        this.connection = connection;
        this.queue = Promise.resolve();
    }

    static open(filename = ':memory:') {
        return new Promise((resolve, reject) => {
            const connection = new sqlite3.Database(filename, (err) => {
                if (err) return reject(err);
                resolve(new Database(connection));
            });
        });
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.connection.exec(sql, (err) => (err ? reject(err) : resolve()));
        });
    }

    transaction(work) {
        const result = this.queue.then(async () => {
            await this.run('BEGIN');
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

    close() {
        return new Promise((resolve, reject) => {
            this.connection.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

module.exports = Database;
