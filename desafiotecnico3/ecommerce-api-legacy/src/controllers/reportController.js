class ReportController {
    constructor({ reportService }) { this.reportService = reportService; }

    financialReport = async (req, res) => {
        res.json(await this.reportService.financialReport());
    };
}

module.exports = ReportController;
