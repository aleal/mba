// Configuração lida de variáveis de ambiente. Nenhum segredo tem default real.
module.exports = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    adminToken: process.env.ADMIN_TOKEN || '',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    logLevel: process.env.LOG_LEVEL || 'info',
});
