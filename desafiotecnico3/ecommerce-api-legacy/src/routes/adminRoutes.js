const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

module.exports = (controller, requireAdmin) => express.Router()
    .get('/api/admin/financial-report', requireAdmin, asyncHandler(controller.financialReport));
