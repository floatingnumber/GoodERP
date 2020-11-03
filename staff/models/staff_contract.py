from odoo import fields, models, api


class StaffContract(models.Model):
    _name = 'staff.contract'
    _description = '员工合同'

    staff_id = fields.Many2one('staff', '员工', required=True)

    over_date = fields.Date('到期日', required=True)
    basic_wage = fields.Float('基础工资')
    endowment = fields.Float('个人养老保险')
    health = fields.Float('个人医疗保险')
    unemployment = fields.Float('个人失业保险')
    housing_fund = fields.Float('个人住房公积金')
    endowment_co = fields.Float('公司养老保险',
                                help='公司承担的养老保险')
    health_co = fields.Float('公司医疗保险',
                             help='公司承担的医疗保险')
    unemployment_co = fields.Float('公司失业保险',
                                   help='公司承担的失业保险')
    injury = fields.Float('公司工伤保险',
                          help='公司承担的工伤保险')
    maternity = fields.Float('公司生育保险',
                             help='公司承担的生育保险')
    housing_fund_co = fields.Float('公司住房公积金',
                                   help='公司承担的住房公积金')
    job_id = fields.Many2one('staff.job', '岗位', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        change_default=True,
        default=lambda self: self.env.company)

    @api.onchange('basic_wage')
    def onchange_basic_wage(self):
        # 选择基本工资时带出五险一金比例，计算出应交金额并填充
        if self.basic_wage:
            company = self.env.company
            self.endowment = company.endowment_ratio * 0.01 * self.basic_wage
            self.health = company.health_ratio * 0.01 * self.basic_wage
            self.unemployment = company.unemployment_ratio * 0.01 * self.basic_wage
            self.housing_fund = company.housing_fund_ratio * 0.01 * self.basic_wage
            self.endowment_co = company.endowment_co_ratio * 0.01 * self.basic_wage
            self.health_co = company.health_co_ratio * 0.01 * self.basic_wage
            self.unemployment_co = company.unemployment_co_ratio * 0.01 * self.basic_wage
            self.injury = company.injury_ratio * 0.01 * self.basic_wage
            self.maternity = company.maternity_ratio * 0.01 * self.basic_wage
            self.housing_fund_co = company.housing_fund_co_ratio * 0.01 * self.basic_wage


class ResCompany(models.Model):
    _inherit = 'res.company'

    endowment_ratio = fields.Float('个人养老保险比例（%）')
    health_ratio = fields.Float('个人医疗保险比例（%）')
    unemployment_ratio = fields.Float('个人失业保险比例（%）')
    housing_fund_ratio = fields.Float('个人住房公积金比例（%）')
    endowment_co_ratio = fields.Float('公司养老保险比例（%）',
                                      help='公司承担的养老保险比例')
    health_co_ratio = fields.Float('公司医疗保险比例（%）',
                                   help='公司承担的医疗保险比例')
    unemployment_co_ratio = fields.Float('公司失业保险比例（%）',
                                         help='公司承担的失业保险比例')
    injury_ratio = fields.Float('公司工伤保险比例（%）',
                                help='公司承担的工伤保险比例')
    maternity_ratio = fields.Float('公司生育保险比例（%）',
                                   help='公司承担的生育保险比例')
    housing_fund_co_ratio = fields.Float('公司住房公积金比例（%）',
                                        help='公司承担的住房公积金比例')
