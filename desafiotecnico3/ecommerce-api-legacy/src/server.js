const express = require('express');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const PaymentService = require('./services/paymentService');
const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');
const { hashPassword } = require('./services/passwordService');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');
const checkoutRoutes = require('./routes/checkoutRoutes');
const adminRoutes = require('./routes/adminRoutes');
const userRoutes = require('./routes/userRoutes');
const { requireAdmin } = require('./middlewares/auth');
const { createErrorHandler } = require('./middlewares/errorHandler');

// Composition root: monta models, services, controllers e rotas com as dependências injetadas.
function createApp({ db, config, logger }) {
    const users = new UserModel(db);
    const courses = new CourseModel(db);
    const checkoutService = new CheckoutService({
        db,
        users,
        courses,
        enrollments: new EnrollmentModel(db),
        payments: new PaymentModel(db),
        auditLogs: new AuditLogModel(db),
        paymentService: new PaymentService({ gatewayKey: config.paymentGatewayKey, logger }),
        hashPassword,
    });
    const adminOnly = requireAdmin(config.adminToken);

    const app = express();
    app.use(express.json());
    app.use(checkoutRoutes(new CheckoutController({ checkoutService })));
    app.use(adminRoutes(new ReportController({ reportService: new ReportService({ courses }) }), adminOnly));
    app.use(userRoutes(new UserController({ users }), adminOnly));
    app.use(createErrorHandler(logger));
    return app;
}

module.exports = { createApp };
