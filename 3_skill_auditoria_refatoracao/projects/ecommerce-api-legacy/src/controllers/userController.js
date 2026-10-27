const userModel = require('../models/userModel');
const { NotFoundError } = require('../errors');
const { parsePositiveInt } = require('./validation');

function createUserController({ db }) {
    return {
        async remove(req, res) {
            const id = parsePositiveInt(req.params.id);
            const deleted = await db.transaction((tx) => userModel.deleteById(tx, id));
            if (!deleted) throw new NotFoundError('Usuário não encontrado');
            res.send('Usuário deletado, junto com suas matrículas e pagamentos.');
        },
    };
}

module.exports = { createUserController };
