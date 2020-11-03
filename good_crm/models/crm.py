
from odoo import api, fields, models


class Opportunity(models.Model):
    _name = 'opportunity'
    _inherits = {'task': 'task_id'}
    _inherit = ['mail.thread']
    _order = 'planned_revenue desc, priority desc, id'
    _description = '商机'

    @api.model
    def _select_objects(self):
        records = self.env['business.data.table'].search([])
        models = self.env['ir.model'].search(
            [('model', 'in', [record.name for record in records])])
        return [(model.model, model.name) for model in models]

    @api.depends('line_ids.price', 'line_ids.quantity')
    def _compute_total_amount(selfs):
        """
        计算报价总额
        :return:
        """
        for self in selfs:
            self.total_amount = sum(
                line.price * line.quantity for line in self.line_ids)

    task_id = fields.Many2one('task',
                              '任务',
                              ondelete='cascade',
                              required=True)
    planned_revenue = fields.Float('预期收益',
                                   track_visibility='always')
    ref = fields.Reference(string='相关记录',
                           selection='_select_objects')
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        change_default=True,
        default=lambda self: self.env.company)
    partner_id = fields.Many2one(
        'partner',
        '客户',
        ondelete='restrict',
        help='待签约合同的客户',
    )
    date = fields.Date('预计采购时间')
    line_ids = fields.One2many(
        'goods.quotation',
        'opportunity_id',
        string='商品报价',
        copy=True,
    )
    total_amount = fields.Float(
        '报价总额',
        track_visibility='always',
        compute='_compute_total_amount',
    )
    success_reason_id = fields.Many2one(
        'core.value',
        '成功原因',
        ondelete='restrict',
        domain=[('type', '=', 'success_reason')],
        context={'type': 'success_reason'},
        help='成功原因分析',
    )

    def assign_to_me(self):
        ''' 继承任务 指派给自己，将商机指派给自己，并修改状态 '''
        for o in self:
            o.task_id.assign_to_me()


class GoodsQuotation(models.Model):
    _name = 'goods.quotation'
    _description = '商品报价'

    opportunity_id = fields.Many2one('opportunity',
                                     '商机',
                                     index=True,
                                     required=True,
                                     ondelete='cascade',
                                     help='关联的商机')
    goods_id = fields.Many2one('goods',
                               '商品',
                               ondelete='restrict',
                               help='商品')
    quantity = fields.Float('数量',
                            default=1,
                            digits='Quantity',
                            help='数量')
    price = fields.Float('单价',
                         required=True,
                         digits='Price',
                         help='商品报价')
    note = fields.Char('描述',
                       help='商品描述')
