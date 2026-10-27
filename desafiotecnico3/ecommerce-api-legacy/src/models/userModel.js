class UserModel {
    constructor(db) { this.db = db; }

    findByEmail(email) {
        return this.db.get('SELECT id FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passwordHash }) {
        const { lastID } = await this.db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
        return lastID;
    }

    // Matrículas e pagamentos do usuário são removidos via ON DELETE CASCADE.
    deleteById(id) {
        return this.db.transaction(() => this.db.run('DELETE FROM users WHERE id = ?', [id]));
    }
}

module.exports = UserModel;
