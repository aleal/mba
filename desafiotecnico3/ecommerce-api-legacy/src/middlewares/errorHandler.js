const { AppError } = require('../utils/errors');

const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// Respostas de erro em texto puro, no mesmo formato da API original.
function createErrorHandler(logger) {
    // O Express reconhece handlers de erro pela aridade 4: `next` precisa estar na assinatura.
    return (err, req, res, next) => {
        if (err instanceof AppError) return res.status(err.status).send(err.message);
        if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');
        logger.error(`${req.method} ${req.originalUrl} falhou:`, err);
        res.status(500).send('Erro interno');
    };
}

module.exports = { asyncHandler, createErrorHandler };
