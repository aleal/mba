const crypto = require('node:crypto');
const { AppError } = require('../utils/errors');

function tokensMatch(provided, expected) {
    const a = Buffer.from(provided);
    const b = Buffer.from(expected);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
}

// Sem ADMIN_TOKEN configurado, as rotas administrativas ficam sempre bloqueadas.
function requireAdmin(adminToken) {
    return (req, res, next) => {
        const provided = req.get('X-Admin-Token') || '';
        if (!adminToken || !tokensMatch(provided, adminToken)) return next(new AppError('Acesso negado', 403));
        next();
    };
}

module.exports = { requireAdmin };
