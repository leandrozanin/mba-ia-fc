const crypto = require('crypto');
const { UnauthorizedError } = require('../errors');

function digest(value) {
    return crypto.createHash('sha256').update(value).digest();
}

// Exige "Authorization: Bearer <ADMIN_TOKEN>"; compara em tempo constante.
function createAdminAuth({ adminToken }) {
    const expected = digest(adminToken);

    return (req, res, next) => {
        const match = /^Bearer (.+)$/.exec(req.get('authorization') || '');
        if (!match || !crypto.timingSafeEqual(digest(match[1]), expected)) {
            return next(new UnauthorizedError());
        }
        next();
    };
}

module.exports = { createAdminAuth };
