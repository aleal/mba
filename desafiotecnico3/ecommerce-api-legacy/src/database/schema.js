const { PAYMENT_STATUS } = require('../models/paymentModel');

const SCHEMA = `
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pass TEXT);
    CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL,
        status TEXT
    );
    CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

async function initSchema(db) {
    await db.exec(SCHEMA);
}

// Dados iniciais de desenvolvimento; só roda em banco vazio.
async function seed(db, { hashPassword }) {
    const { total } = await db.get('SELECT COUNT(*) AS total FROM users');
    if (total > 0) return;

    await db.transaction(async () => {
        await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', await hashPassword('123')]);
        await db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
        await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)', [PAYMENT_STATUS.PAID]);
    });
}

module.exports = { initSchema, seed };
