const sqlite3 = require('sqlite3');

// Wrapper com Promises sobre o driver sqlite3 (API de callbacks).
// A conexão é única: transações e escritas passam por uma fila (mutex) para que
// requisições concorrentes não intercalem comandos dentro de um BEGIN/COMMIT.
function openDatabase(path) {
    return new Promise((resolve, reject) => {
        const raw = new sqlite3.Database(path, (err) => (err ? reject(err) : resolve(wrap(raw))));
    });
}

function wrap(raw) {
    const run = (sql, params = []) => new Promise((resolve, reject) => {
        raw.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params = []) => new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
    const all = (sql, params = []) => new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
    const exec = (sql) => new Promise((resolve, reject) => {
        raw.exec(sql, (err) => (err ? reject(err) : resolve()));
    });
    const close = () => new Promise((resolve, reject) => {
        raw.close((err) => (err ? reject(err) : resolve()));
    });

    let queue = Promise.resolve();
    function exclusive(work) {
        const result = queue.then(work);
        queue = result.catch(() => {});
        return result;
    }

    function transaction(work) {
        return exclusive(async () => {
            await run('BEGIN');
            try {
                const result = await work();
                await run('COMMIT');
                return result;
            } catch (err) {
                await run('ROLLBACK');
                throw err;
            }
        });
    }

    return { run, get, all, exec, close, transaction };
}

module.exports = { openDatabase };
