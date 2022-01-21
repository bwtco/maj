from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import datetime, timedelta


class purchaseConsumption(models.Model):
    _name = 'purchase.consumption'
    _description = 'Purchase Consumption'

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        if st_id:
            return st_id.id

    is_use = fields.Boolean('Use')
    name = fields.Char('consumption No.')
    group_id = fields.Many2one('project.task', 'Task Group')
    task_id = fields.Many2one('project.task', 'Task')
    flag = fields.Boolean('Flag', default=False)
    material_id = fields.Many2one('product.product', 'Material')
    consumption_date = fields.Date(
        'Date', default=fields.date.today(), required=True)
    requirement_date = fields.Date('Requirement Date')
    procurement_date = fields.Date('Procurement Date')
    quantity = fields.Integer(' Quantity')
    specification = fields.Char('Specification')
    remark = fields.Char('Remark')
    model = fields.Char('Related Document Model', index=1)
    mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage',
                                domain=lambda self: [('model', '=', self._name)], auto_join=True, readonly=True)
    # previous quantity fields
    total_approved_qty = fields.Float('Approved Qty', readonly=True)
    total_ordered_qty = fields.Float('Ordered Qty', readonly=True)
    consumption_qty = fields.Float('consumption Qty')
    balance_qty = fields.Float('Balance Qty', compute='get_balanced_qty')

    # latest as suggested on 26/12/16 quantity fields
    estimated_qty = fields.Float('Estimated Qty')
    consumption_as_on_date = fields.Float('Consumption as on date')
    current_consum_qty = fields.Float('Current consumption Qty')
    consumption_ids = fields.One2many(
        'purchase.consumption.line', 'order_id')
    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], 'Status')
    priority = fields.Selection([('high', 'High'), ('low', 'Low')], 'Priority')
    brand_id = fields.Many2one('brand.brand', 'Brand')
    consumption_type = fields.Selection(
        [('estimated', 'Estimated'), ('non_estimated', 'Non Estimated')], 'Type')
    unit = fields.Many2one('uom.uom', 'Unit', required=True)
    rate = fields.Float('Rate')
    procurement_type = fields.Selection([('New Purchase from Supplier', 'New Purchase from Supplier'),
                                         ('Cash Purchase ', 'Cash Purchase '),
                                         ('IST from other sites', 'IST from other sites'), ], "Procurement Type")
    warehouse_id = fields.Char('Procurement Type', readonly=True)
    product_location_id = fields.Many2one('stock.location', "Location")
    purchase_ids = fields.Many2many(
        'purchase.order', 'po_consumption_rel1', 'consumption_id', 'purchase_id', string='Purchase Orders')
    consumption_fulfill = fields.Boolean(
        'Req fulfill', compute='is_consumption_fulfill')
    stage_id = fields.Many2one(
        'stage.master', 'Stage', default=_default_stage, readonly=True, copy=False, track_visibility='onchange')
    project_wbs = fields.Many2one('project.task', 'project WBS', domain=[
        ('is_wbs', '=', True), ('is_task', '=', False)])
    project_id = fields.Many2one('project.project', 'Project')

    sub_project = fields.Many2one('sub.project', 'Sub Project')
    estimation_id = fields.Many2one('task.material.line', 'Estimate No.')

    material_category = fields.Many2one(
        'product.category', string='Material Category', related='material_id.categ_id', store=True)
    related_task_category = fields.Many2one(
        'task.category', related='task_id.category_id', store=True)
    task_category = fields.Many2many(
        'task.category', 'purchase_cons_req_task_cat_rel', 'purchase_req_id', 'task_category_id',
        string='Task Category')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    me_sequence = fields.Char(readonly=True)
    counter = 0

    @api.depends('current_consum_qty', 'total_ordered_qty')
    def get_balanced_qty(self):
        for id in self:
            id.balance_qty = id.quantity - \
                             (id.current_consum_qty + id.consumption_as_on_date)

    @api.depends('current_consum_qty')
    @api.onchange('current_consum_qty')
    def validate_req_qty(self):
        self.balance_qty = self.quantity - \
                           (self.total_ordered_qty + self.current_consum_qty)
        if self.balance_qty < 0.0:
            raise UserError(_('Invalid Current consumption Qty'))

    # remove counter
    def change_state(self, context={}):
        if self.counter == 0:
            """Updating consumption till date in estimation table"""

            requisition_till_date = self.current_consum_qty
            if requisition_till_date <= self.estimation_id.material_uom_qty:

                self.name = self.env['ir.sequence'].sudo().next_by_code('purchase.consumption') or '/'
                # self.flag_consumption = 1

            else:
                # self.flag_consumption = 0
                raise UserError(
                    _('Sorry you cannot approve consumption greater then available quantity !'))

            # self.counter = self.counter + 1
            if context.get('copy'):
                self.write({'state': 'confirm'})
                if self.product_location_id:

                    # Create Stock moves on Confirmation instaed of Creation.
                    location = self.env['stock.location'].search(
                        [('usage', '=', 'production')], limit=1)
                    project_location = self.env['stock.location'].search(
                        [('project_id', '=', self.project_id.id)], limit=1)
                    loc_id = False
                    loc_dest_id = False
                    if not project_location:
                        loc_id = self.product_location_id.id
                        loc_dest_id = location.id
                    else:
                        loc_id = self.product_location_id.id
                        loc_dest_id = project_location.id
                    stock_move_obj = self.env['stock.move'].create({
                        'name': self.name or 'CONSUMT',
                        'location_id': loc_id,
                        'location_dest_id': loc_dest_id,
                        'product_id': self.material_id.id,
                        'product_uom': self.unit.id,
                        'product_uom_qty': self.current_consum_qty,
                        'quantity_done': self.current_consum_qty,
                        'origin': self.name or 'CONSUMT',
                    })
                    if stock_move_obj:
                        stock_move_line_values = {
                            'date': datetime.today(),
                            'product_uom_qty': self.current_consum_qty,
                            'product_id': self.material_id.id,
                            'product_uom_id': self.unit.id,
                            'location_id': loc_id,
                            'location_dest_id': loc_dest_id,
                            'company_id': self.env.user.company_id.id,
                            'reference': self.name or 'CONSUMT',
                            'move_id': stock_move_obj.id,
                            'qty_done': self.current_consum_qty
                        }

                        stock_move_obj._action_confirm()
                        stock_move_obj._action_assign()
                        stock_move_obj.write({'state': 'done'})

                    location_ids = self.env['stock.quant'].search(
                        [('product_id.id', '=', self.material_id.id),
                         ('location_id', '=', self.product_location_id.id)])

                    for id in location_ids:
                        id.sudo().reserved_quantity = id.reserved_quantity - \
                                                      (self.current_consum_qty)
                        id.sudo().quantity = id.quantity - self.current_consum_qty

            view_id = self.env.ref(
                'pragtech_purchase.approval_wizard_form_view_purchase').id
            return {

                'type': 'ir.actions.act_window',
                'key2': 'client_action_multi',
                'res_model': "approval.wizard",
                'multi': "True",
                'target': 'new',
                'views': [[view_id, 'form']],
            }


class PurchaseConsumptionLine(models.Model):
    _name = 'purchase.consumption.line'
    material_id = fields.Many2one('product.product', 'Material')
    unit = fields.Many2one('uom.uom', 'Unit', required=True)
    rate = fields.Float('Rate')
    quantity = fields.Integer('Quantity')
    total_ordered_qty = fields.Float('Ordered Qty', readonly=True)
    balance_qty = fields.Float('Balance Qty', compute='get_balanced_qty')
    consumption_as_on_date = fields.Float('Consumption as on date')
    current_consum_qty = fields.Float('Current consumption Qty')
    order_id = fields.Many2one(
        'purchase.consumption', 'consumption_ids')

    @api.depends('current_consum_qty', 'total_ordered_qty')
    def get_balanced_qty(self):
        self.balance_qty = self.order_id.current_consum_qty - \
                           self.order_id.total_ordered_qty
        self.current_consum_qty = self.order_id.current_consum_qty
        self.total_ordered_qty = self.order_id.total_ordered_qty
