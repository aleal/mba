const config = require('./config');
const { createLogger } = require('./utils/logger');
const { openDatabase } = require('./database/connection');
const { initSchema, seed } = require('./database/schema');
const { hashPassword } = require('./services/passwordService');
const { createApp } = require('./server');

const logger = createLogger(config.logLevel);

(async () => {
    const db = await openDatabase(config.dbPath);
    await initSchema(db);
    await seed(db, { hashPassword });

    if (!config.adminToken) logger.warn('ADMIN_TOKEN não definido: rotas administrativas responderão 403.');

    createApp({ db, config, logger }).listen(config.port, () => {
        logger.info(`LMS API rodando na porta ${config.port}`);
    });
})().catch((err) => {
    logger.error('Falha ao iniciar a aplicação:', err);
    process.exit(1);
});
