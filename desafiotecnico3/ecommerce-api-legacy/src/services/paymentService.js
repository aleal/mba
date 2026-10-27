const { PAYMENT_STATUS } = require('../models/paymentModel');

// Gateway simulado: cartões iniciados por este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

class PaymentService {
    constructor({ gatewayKey, logger }) {
        this.gatewayKey = gatewayKey;
        this.logger = logger;
    }

    authorize(cardNumber) {
        this.logger.info(`Processando pagamento do cartão final ${cardNumber.slice(-4)}`);
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    }
}

module.exports = PaymentService;
