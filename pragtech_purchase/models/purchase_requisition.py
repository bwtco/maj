from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class purchaseRequisition(models.Model):
    _name = 'purchase.requisition'
    _description = 'Purchase Requisition'

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        if st_id:
            return st_id.id

    is_use = fields.Boolean('Use')
    name = fields.Char('Requisition No.')
    group_id = fields.Many2one('project.task', 'Task Group')
    task_id = fields.Many2one('project.task', 'Task')
    flag = fields.Boolean('Flag', default=False)
    material_id = fields.Many2one('product.product', 'Material')
    requisition_date = fields.Date(
        'Date', default=fields.date.today(), required=True)
    requirement_date = fields.Date('Requirement Date')
    procurement_date = fields.Date('Procurement Date')
    quantity = fields.Integer(' Quantity')
    specification = fields.Char('Specification')
    remark = fields.Char('Remark')
    model = fields.Char('Related Document Model', index=1)
    mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage', domain=lambda self: [('model', '=', self._name)], auto_join=True,readonly=True)
    # previous quantity fields
    total_approved_qty = fields.Float('Approved Qty', readonly=True)
    total_ordered_qty = fields.Float('Ordered Qty', readonly=True)
    requisition_qty = fields.Float('Requisition Qty')
    balance_qty = fields.Float('Balance Qty', compute='get_balanced_qty')

    # latest as suggested on 26/12/16 quantity fields
    estimated_qty = fields.Float('Estimated Qty')
    Requisition_as_on_date = fields.Float('Requisition as on date')
    current_req_qty = fields.Float('Current requisition Qty')

    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], 'Status')
    priority = fields.Selection([('high', 'High'), ('low', 'Low')], 'Priority')
    brand_id = fields.Many2one('brand.brand', 'Brand')
    requisition_type = fields.Selection(
        [('estimated', 'Estimated'), ('non_estimated', 'Non Estimated')], 'Type')
    unit = fields.Many2one('uom.uom', 'Unit', required=True)
    rate = fields.Float('Rate')
    procurement_type = fields.Selection([('New Purchase from Supplier', 'New Purchase from Supplier'),
                                         ('Cash Purchase ', 'Cash Purchase '),
                                         ('IST from other sites', 'IST from other sites'), ], "Procurement Type")
    warehouse_id = fields.Char('Procurement Type', readonly=True)
    purchase_ids = fields.Many2many(
        'purchase.order', 'po_requisition_rel1', 'requisition_id', 'purchase_id', string='Purchase Orders')
    requisition_fulfill = fields.Boolean(
        'Req fulfill', compute='is_requisition_fulfill')
    stage_id = fields.Many2one(
        'stage.master', 'Stage', default=_default_stage, readonly=True, copy=False, track_visibility='onchange')
    project_wbs = fields.Many2one('project.task', 'project WBS', domain=[
                                  ('is_wbs', '=', True), ('is_task', '=', False)])
    project_id = fields.Many2one('project.project', 'Project')

    sub_project = fields.Many2one('sub.project', 'Sub Project')
    estimation_id = fields.Many2one('task.material.line', 'Estimate No.')

    material_category = fields.Many2one(
        'product.category', string='Material Category', related='material_id.categ_id', store=True)
    related_task_category=fields.Many2one('task.category',related='task_id.category_id', store=True)
    task_category = fields.Many2many(
        'task.category', 'purchase_req_task_cat_rel', 'purchase_req_id', 'task_category_id', string='Task Category')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    me_sequence = fields.Char(readonly=True)
    counter = fields.Integer('counter')

    @api.depends('current_req_qty', 'total_ordered_qty')
    def get_balanced_qty(self):
        self.balance_qty = self.current_req_qty - self.total_ordered_qty

    @api.depends('current_req_qty')
    @api.onchange('current_req_qty')
    def validate_req_qty(self):
        self.balance_qty = self.quantity - \
            (self.total_ordered_qty + self.current_req_qty)
        if self.balance_qty < 0.0:
            raise UserError(_('Invalid Current requisition Qty'))


#     @api.model
#     def create(self, vals):
#         if vals.get('name', 'New') == 'New':
#             vals['name'] = self.env['ir.sequence'].next_by_code('purchase.requisition') or '/'
#         existing_stage = []
#         st_id = self.env['stage.master'].search([('draft', '=', True)])
#         msg_ids = {
#             'date': datetime.now(),
#             'from_stage': None,
#             'to_stage': st_id.id,
#             'remark': None,
#             'model': 'purchase.requisition'
#         }
#         existing_stage.append((0, 0, msg_ids))
#         vals.update({'mesge_ids': existing_stage})
#         return super(purchaseRequisition, self).create(vals)

    def unlink(self):
        ids = []
        for line in self:
            ids.append(line.id)
        Purchase_order_obj = self.env['po.requisition'].search(
            [('requisition_id', 'in', ids)])
        if Purchase_order_obj:
            raise UserError(
                _('You cannot delete Requisition which is used in Purchase Order .'))

    @api.model
    def is_requisition_fulfill(self):
        total_qty = 0
        po_line_obj = self.env['purchase.order.line'].search(
            [('requisition_id', '=', self.id)])
        for line in po_line_obj:
            total_qty = +line.product_qty
        if total_qty > self.quantity:
            res = self.update({'requsition_fulfill': True})
            return True

    def change_state_1(self,context={}):

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

    def change_state(self, context={}):
        if self.counter == 0:
            self.counter = self.counter + 1
            if context.get('copy') == True:
                self.write({'state': 'confirm'})

            """Updating Requisition till date in estimation table"""

            requisition_till_date = self.estimation_id.requisition_till_date + \
                                    self.current_req_qty
            if requisition_till_date <= self.estimation_id.material_uom_qty:
                self.estimation_id.requisition_till_date = self.estimation_id.requisition_till_date + \
                                                           self.current_req_qty

                self.name = self.env['ir.sequence'].next_by_code(
                    'purchase.requisition') or '/'
                self.flag = 1

            else:
                self.flag = 0
                raise UserError(
                    _('Sorry you cannot approve requisition greater then available quantity !'))
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
