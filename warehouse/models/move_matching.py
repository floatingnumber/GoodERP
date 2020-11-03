
from odoo.osv import osv

from .utils import safe_division
from odoo import models, fields, api
from odoo.exceptions import UserError


class WhMoveMatching(models.Model):
    _name = 'wh.move.matching'
    _description = '匹配记录'

    line_in_id = fields.Many2one(
        'wh.move.line', '入库',
        ondelete='set null', index=True,
        help='入库单行')
    line_out_id = fields.Many2one(
        'wh.move.line', '出库',
        ondelete='set null', index=True,
        help='出库单行')
    qty = fields.Float(
        '数量',
        digits='Quantity', required=True,
        help='出库单行商品的数量')
    uos_qty = fields.Float(
        '辅助数量',
        digits='Quantity', required=True,
        help='出库单行商品的辅助数量')
    expiration_date = fields.Date(
        '过保日',
        help='商品保质期截止日期')
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        change_default=True,
        default=lambda self: self.env.company)

    def create_matching(self, line_in_id, line_out_id, qty, uos_qty, expiration_date):
        res = {
            'line_out_id': line_out_id,
            'line_in_id': line_in_id,
            'qty': qty,
            'uos_qty': uos_qty,
            'expiration_date': expiration_date,
        }

        return self.create(res)


class WhMoveLine(models.Model):
    _inherit = 'wh.move.line'

    qty_remaining = fields.Float(
        compute='_get_qty_remaining',
        string='剩余数量',
        digits='Quantity',
        index=True, store=True, readonly=True,
        help='商品的剩余数量')
    uos_qty_remaining = fields.Float(
        compute='_get_qty_remaining', string='剩余辅助数量',
        digits='Quantity',
        index=True, store=True, readonly=True,
        help='商品的剩余辅助数量')

    matching_in_ids = fields.One2many(
        'wh.move.matching', 'line_in_id', string='关联的入库',
        help='关联的入库单行')
    matching_out_ids = fields.One2many(
        'wh.move.matching', 'line_out_id', string='关联的出库',
        help='关联的出库单行')

    @api.depends('goods_qty', 'matching_in_ids.qty', 'matching_in_ids.uos_qty')
    def _get_qty_remaining(self):
        for wml in self:
            wml.qty_remaining = wml.goods_qty - \
                sum(match.qty for match in wml.matching_in_ids)
            wml.uos_qty_remaining = wml.goods_uos_qty - \
                sum(match.uos_qty for match in wml.matching_in_ids)

    def create_matching_obj(self, line, matching):
        matching_obj = self.env['wh.move.matching']
        matching_obj.create_matching(
            matching.get('line_in_id'),
            line.id, matching.get('qty'),
            matching.get('uos_qty'),
            matching.get('expiration_date'),
        )

    def prev_action_done(self):
        """
            发货 matching
        """
        for line in self:
            if line.warehouse_id.type == 'stock' and \
                    line.goods_id.is_using_matching():
                if line.goods_id.is_using_batch() and line.lot_id:
                    matching_records, cost = \
                        line.goods_id.get_matching_records_by_lot(
                            line.lot_id, line.goods_qty, line.goods_uos_qty)
                    for matching in matching_records:
                        self.create_matching_obj(line, matching)
                else:
                    matching_records, cost = line.goods_id \
                        .get_matching_records(
                        line.warehouse_id, line.goods_qty,
                        uos_qty = line.goods_uos_qty,
                        attribute = line.attribute_id,
                        move_line = line)
                    for matching in matching_records:
                        self.create_matching_obj(line, matching)
                line.cost_unit = safe_division(cost, line.goods_qty)
                line.cost = cost
                # 将过保日填充到出库明细行
                line.expiration_date = matching_records and matching_records[0].get(
                    'expiration_date')

        return super(WhMoveLine, self).prev_action_done()

    def prev_action_draft(self):
        for line in self:
            if line.qty_remaining != line.goods_qty:
                raise UserError('当前的入库已经被其他出库匹配，请先取消相关的出库')

            line.matching_in_ids.unlink()
            line.matching_out_ids.unlink()
            line.expiration_date = False

        return super(WhMoveLine, self).prev_action_draft()
