from odoo import models, fields, api
from odoo.exceptions import UserError

class UnbilledGrnWizard(models.TransientModel):
    _name = 'unbilled.grn.wizard'
    _description = 'Unbilled GRN'

    project_id = fields.Many2one('project.project', 'Project')
    sub_project = fields.Many2one('sub.project', 'Sub Project')
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
    project_wbs = fields.Many2one('project.task', 'Project WBS', domain=[
                                  ('is_wbs', '=', True), ('is_task', '=', False)])
    partner_id = fields.Many2one('res.partner', 'Vendor')
    stage_id = fields.Many2one('stage.master', 'Stage')
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    order_line = fields.One2many(
        'unbilled.grn.lines.wizard', 'order_id', string='Order Lines', copy=True, ondelete='cascade')

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            return {'domain': {'sub_project': [('project_id', '=', self.project_id.id)],
                               'project_wbs': [('project_id', '=', self.project_id.id), ('is_wbs', '=', True), ('is_task', '=', False), ('is_group', '=', False)],
                               'purchase_order_id': [('project_id', '=', self.project_id.id)], }}

    @api.onchange('sub_project')
    def onchange_sub_project_id(self):
        if self.sub_project:
            return {'domain': {'project_wbs': [('sub_project', '=', self.sub_project.id), ('is_wbs', '=', True), ('is_task', '=', False), ('is_group', '=', False)],
                               'purchase_order_id': [('sub_project', '=', self.sub_project.id)], }}

    @api.onchange('project_wbs')
    def onchange_project_wbs(self):
        if self.project_wbs:
            return {'domain': {'puchase_order_id': [('project_wbs', '=', self.project_wbs.id)], }}

    def compute_purchase_orders(self):
        self.order_line.unlink()
        if self.from_date > self.to_date:
            raise UserError("From Date should be lesser than To Date")
        domain = []
        if self.project_id:
            domain.append(('project_id', '=', self.project_id.id))
        if self.sub_project:
            domain.append(('sub_project', '=', self.sub_project.id))
        if self.project_wbs:
            domain.append(('project_wbs', '=', self.project_wbs.id))
        if self.purchase_order_id:
            domain.append(('id', '=', self.purchase_order_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.stage_id:
            domain.append(('stage_id', '=', self.stage_id.id))
        if self.from_date:
            domain.append(('date_order', '>=', self.from_date))
        if self.to_date:
            domain.append(('date_order', '<=', self.to_date))
        domain.append(('state', 'in', ['shipment', 'purchase', 'done']))
        po_obj = self.env['purchase.order'].search(domain)
        vals = {}
        for po in po_obj:
            unbilled_qty = 0
            billed_amount = 0.0
            unbilled_amount = 0.0
            for line in po.order_line:
                unbilled_qty = line.qty_received_custom - line.qty_invoiced
                unbilled_amount = unbilled_qty * line.price_unit
                billed_amount = line.qty_invoiced * line.price_unit
                vals = {
                    'project_id': po.project_id.id,
                    'sub_project': po.sub_project.id,
                    'project_wbs': po.project_wbs.id,
                    'purchase_order_id': po.id,
                    'partner_id': po.partner_id.id,
                    #'stage_id': po.stage_id.id,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'recieved_qty': line.qty_received_custom,
                    'billed_qty': line.qty_invoiced,
                    'unbilled_qty': unbilled_qty,
                    'billed_amount': billed_amount,
                    'unbilled_amount': unbilled_amount,
                    'order_id': self.id,
                }
                value = self.order_line.create(vals)
        view_id = self.env.ref(
            'pragtech_purchase.purchase_order_unbilled_grn_wizard_form_view').id
        return {
            'context': self.env.context,
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'unbilled.grn.wizard',
            'res_id': self.id,
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

class UnbilledGrnLinesWizard(models.TransientModel):
    _name = 'unbilled.grn.lines.wizard'
    _description = 'Unbilled GRN Lines'

    project_id = fields.Many2one('project.project', 'Project')
    sub_project = fields.Many2one('sub.project', 'Sub Project')
    project_wbs = fields.Many2one('project.task', 'Project WBS', domain=[
                                  ('is_wbs', '=', True), ('is_task', '=', False)])
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
    partner_id = fields.Many2one('res.partner', 'Vendor')
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Integer("Product Quantity")
    recieved_qty = fields.Integer("Received Quantity")
    billed_qty = fields.Integer("Billed Quantity")
    unbilled_qty = fields.Integer("Unbilled Quantity")
    billed_amount = fields.Float("Billed Amount")
    unbilled_amount = fields.Float("Unbilled Amount")
    order_id = fields.Many2one(
        'unbilled.grn.wizard', string='Order Reference', ondelete='cascade')
