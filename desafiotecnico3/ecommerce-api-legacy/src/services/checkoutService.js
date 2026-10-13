const { AppError } = require('../utils/errors');
const { PAYMENT_STATUS } = require('../models/paymentModel');

class CheckoutService {
    constructor({ db, users, courses, enrollments, payments, auditLogs, paymentService, hashPassword }) {
        Object.assign(this, { db, users, courses, enrollments, payments, auditLogs, paymentService, hashPassword });
    }

    async checkout({ name, email, password, courseId, cardNumber }) {
        const course = await this.courses.findActiveById(courseId);
        if (!course) throw new AppError('Curso não encontrado', 404);

        const status = this.paymentService.authorize(cardNumber);
        if (status === PAYMENT_STATUS.DENIED) throw new AppError('Pagamento recusado', 400);

        // Hash calculado fora da transação para não segurar o lock durante o scrypt.
        const existing = await this.users.findByEmail(email);
        const passwordHash = !existing && password ? await this.hashPassword(password) : null;

        return this.db.transaction(async () => {
            const user = await this.users.findByEmail(email);
            const userId = user ? user.id : await this.users.create({ name, email, passwordHash });
            const enrollmentId = await this.enrollments.create(userId, course.id);
            await this.payments.create(enrollmentId, course.price, status);
            await this.auditLogs.log(`Checkout curso ${course.id} por ${userId}`);
            return { enrollmentId };
        });
    }
}

module.exports = CheckoutService;
