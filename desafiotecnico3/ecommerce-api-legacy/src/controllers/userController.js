const { AppError } = require('../utils/errors');
const { toPositiveInt } = require('../utils/validation');

class UserController {
    constructor({ users }) { this.users = users; }

    remove = async (req, res) => {
        const id = toPositiveInt(req.params.id);
        if (id === null) throw new AppError('Bad Request', 400);
        await this.users.deleteById(id);
        res.send('Usuário deletado.');
    };
}

module.exports = UserController;
