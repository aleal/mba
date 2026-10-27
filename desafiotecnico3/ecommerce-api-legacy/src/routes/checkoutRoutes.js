const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

module.exports = (controller) => express.Router()
    .post('/api/checkout', asyncHandler(controller.checkout));
