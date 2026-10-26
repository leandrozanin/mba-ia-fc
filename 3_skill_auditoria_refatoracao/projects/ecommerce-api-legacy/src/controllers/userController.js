const { notFound } = require('../errors');
const { parseId } = require('./validators');

function createUserController({ db, users, enrollments }) {
    return {
        async remove(rawId) {
            const id = parseId(rawId);
            await db.transaction(async (tx) => {
                if (!(await users.anonymize(tx, id))) throw notFound('Usuário não encontrado');
                await enrollments.audit(tx, `Usuário ${id} anonimizado`);
            });
            return { msg: 'Usuário removido; histórico financeiro preservado sem dados pessoais.' };
        },
    };
}

module.exports = { createUserController };
