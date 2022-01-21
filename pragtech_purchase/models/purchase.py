from datetime import datetime, timedelta
from odoo.tools.float_utils import float_compare
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import UserError
from odoo.tools.translate import _

READONLY_STATES = {
    'purchase': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class POTypes(models.Model):
    _name = 'po.types'
    _description = 'PO Types'

    name = fields.Char('PO Type', required=True)
    remark = fields.Text(string='Remark')
    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], 'Status')


class PriorityTypes(models.Model):
    _name = 'priority.types'
    _description = 'Priority Types'

    name = fields.Char('Priority Type', required=True)
    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], 'Status')


class ProcurementTypes(models.Model):
    _name = 'procurement.types'
    _description = 'Procurement Types'

    name = fields.Char('Procurement Type', required=True)
    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], 'Status')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = 'Purchase Order'

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        if st_id:
            return st_id.id

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    project_wbs = fields.Many2one('project.task', 'Project WBS Name', domain=[
        ('is_wbs', '=', True), ('is_task', '=', False)], required=True)
    project_id = fields.Many2one('project.project', 'Project', required=True)
    sub_project = fields.Many2one('sub.project', 'Sub Project', required=True)
    transaction_count = fields.Integer(
        'Transaction count', compute='_get_count')
    material_category = fields.Many2many(
        'product.category', 'po_category_rel', 'purchase_order_id', 'category_id', string='Material Category')
    material = fields.Many2one('product.product', 'Material')
    from_date = fields.Date(
        'From', default=str(datetime.now() + timedelta(days=-30)))
    to_date = fields.Date('To Date', default=fields.date.today())
    stage_id = fields.Many2one(
        'stage.master', 'Stage', default=_default_stage, copy=False)
    flag = fields.Boolean('Flag', default=False)
    valid_till = fields.Datetime('Valid Till')
    transport_amount = fields.Float('Transport Amount')
    loading_charges = fields.Float('Loading Charges')
    unloading_charges = fields.Float('Unloading Charges')
    other_charges = fields.Float('Other Charges')
    order_line = fields.One2many('purchase.order.line', 'order_id', string='Order Lines', states=READONLY_STATES,
                                 copy=True, ondelete='cascade',
                                 store=True)
    requisition_id = fields.Many2one(
        'purchase.requisition', string='Requisitions')
    type = fields.Selection(
        [('international', 'International'), ('domestic', 'Domestic')], 'Type')
    select_all = fields.Boolean('Select All')
    is_write = fields.Boolean(defalt=False)
    mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage',
                                domain=lambda self: [('model', '=', self._name)], auto_join=True,
                                readonly=True)
    po_requisition_line = fields.One2many(
        'po.requisition', 'order_id', string='Requisition Lines', ondelete='cascade')
    state = fields.Selection([
        ('draft', 'Draft PO'),
        ('amend and draft', 'Amend And Draft'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('shipment', 'Purchase Order'),
        ('purchase', 'Shipment'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, select=True, copy=False, default='draft', track_visibility='onchange')

    #     action_view_invoice

    def _get_count(self):
        transaction = self.env['purchase.transaction']
        transaction_obj = transaction.search(
            [('purchase_order_id', '=', self.id), ('flag', '=', True)])
        count = 0
        for line in transaction_obj:
            count = count + 1
        self.transaction_count = count

    """Return recovery records(tree view)"""

    def get_transactions(self):
        st_id = self.env['stage.master'].search([('approved', '=', True)])
        action = self.env.ref(
            'pragtech_purchase.purchaseorder_action_transaction')
        view_id = self.env.ref(
            'pragtech_purchase.Purchase_Transaction_view_tree').id
        model = 'purchase.transaction'

        return {'name': 'Transactions',
                'domain': [('purchase_order_id', '=', self.id)],
                # 'view_type': action.view_type,
                'view_mode': action.view_mode,
                'res_model': model,
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                }

    #     @api.multi
    #     def _get_count(self):
    #         transaction = self.env['purchase.transaction']
    #         transaction_obj = transaction.search([('purchase_order_id', '=', self.id),('flag','=',True)])
    #         count=0
    #         for line in transaction_obj:
    #             count=count+1
    #         self.transaction_count=count
    #
    #     """Return recovery records(tree view)"""
    #     @api.multi
    #     def get_transactions(self):
    #         recovery_ids=[]
    #         st_id = self.env['stage.master'].search([('approved', '=', True)])
    #
    #         action = self.env.ref('pragtech_purchase.purchaseorder_action_transaction')
    #         view_id = self.env.ref('pragtech_purchase.Purchase_Transaction_view_tree').id
    #         model='purchase.transaction'
    #
    #
    #         return {'name':'Recoveries',
    #             'domain':[('purchase_order_id','=',self.id)],
    #           'view_type': action.view_type,
    #           'view_mode': action.view_mode,
    #           'res_model': model,
    #           'res_id': self.id,
    #           'view_id': False,
    #           'type': 'ir.actions.act_window',
    #           }
    #

    def write(self, vals):
        if vals.get('po_requisition_line'):
            for i in vals.get('po_requisition_line'):
                po_req_obj = self.env['po.requisition'].browse(i[1])
                purchase_order_obj = self.env[
                    'purchase.order'].browse(po_req_obj.order_id.id)
                stage_master_obj = self.env['stage.master'].search(
                    [('amend_and_draft', '=', True)], limit=1)
                if purchase_order_obj.stage_id.approved:
                    vals.update(
                        {'stage_id': stage_master_obj.id, 'flag': False, 'state': 'draft'})
                    vals.update({'state': 'draft'})
                if po_req_obj:
                    if po_req_obj.is_red or (
                            po_req_obj.requisition_qty - po_req_obj.total_ordered_qty) > po_req_obj.current_order_qty:
                        raise UserError(_('Invalid Order Quantity'))
        if vals.get('partner_id'):
            partner = vals.get('partner_id')
            p_id = self.env['res.partner'].browse(partner)
            if p_id.vendor_status == 'trial':
                if p_id.trial_allowed <= p_id.trial_used:
                    pass
        #                     raise UserError(
        #                         _('Vendor Trial Period Has Expired. Can Not Create Purchase Orders Anymore For This Vendor.'))
        res = super(PurchaseOrder, self).write(vals)
        if self.order_line:
            for order_line in self.order_line:
                if order_line.delivery_schedule_line_ids:
                    quantity_to_deliver = 0.0
                    product_qty = order_line.product_qty
                    for schedule_line in order_line.delivery_schedule_line_ids:
                        quantity_to_deliver = quantity_to_deliver + \
                                              schedule_line.quantity_to_deliver
                    if quantity_to_deliver != product_qty:
                        raise UserError(
                            _('Quantity to Deliver should be equal Product Quantity'))
        return res

    @api.model
    def create(self, vals):
        existing_stage = []
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        msg_ids = {
            'date': datetime.now(),
            'from_stage': None,
            'to_stage': st_id.id,
            'remark': 'Created by ' + (self.env['res.users'].browse(self._context.get('uid'))).name,
            'model': 'purchase.order'
        }
        if vals.get('partner_id'):
            partner = vals.get('partner_id')
            p_id = self.env['res.partner'].browse(partner)
            p_id._get_trial()
            if p_id.vendor_status == 'trial':
                if p_id.trial_allowed <= p_id.trial_used:
                    pass
        #                     raise UserError(
        #                         _('Vendor Trial Period Has Expired. Can Not Create Purchase Orders Anymore For This Vendor.'))
        existing_stage.append((0, 0, msg_ids))
        vals.update({'mesge_ids': existing_stage})
        res = super(PurchaseOrder, self).create(vals)
        if self.order_line:
            for order_line in self.order_line:
                if order_line.delivery_schedule_line_ids:
                    quantity_to_deliver = 0.0
                    product_qty = order_line.product_qty
                    for schedule_line in order_line.delivery_schedule_line_ids:
                        quantity_to_deliver = quantity_to_deliver + \
                                              schedule_line.quantity_to_deliver
                    if quantity_to_deliver != product_qty:
                        raise UserError(
                            _('Quantity to Deliver should be equal Product Quantity'))
        return res

    # Set default Project and WBS if already set in PO.
    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if self.project_id and self.project_wbs:
            res['project_id'] = self.project_id
            res['project_wbs_id'] = self.project_wbs
        return res

    def get_seller_price(self, product_id):
        product_obj = self.env['product.product'].search(
            [('id', '=', product_id)])
        seller_cost = 0
        for seller_id in product_obj.seller_ids:
            if seller_id.name.id == self.partner_id.id:
                seller_cost = seller_id.price
        return seller_cost

    @api.depends('state', 'move_ids.state')
    def custom_compute_qty_received(self, product_id):
        total = 0
        picking = self.env['stock.picking'].search(
            [('state', '=', 'done'), ('origin', '=', self.name), ('partner_id', '=', self.partner_id.id)])
        for pickings in picking:
            for line in pickings.pack_operation_product_ids:
                if line.product_id.id == product_id:
                    total = line.qty_done
        return total

    """ Reflects the changes of PO requisition on Purchase Order Lines"""

    @api.onchange('po_requisition_line', 'po_requisition_line.specification', 'po_requisition_line.current_order_qty')
    def onchange_po_requisition(self):
        material_id_list = []
        rate = 0
        data_lst = []
        for line in self.po_requisition_line:
            material_id_list.append(line.material_id)
            """if invalid order qty then color will change to red."""
            if line.current_order_qty > (line.requisition_qty - line.total_ordered_qty) or line.current_order_qty <= 0:
                line.write({'is_red': True})
            else:
                line.write({'is_red': False})

        for line in list(set(material_id_list)):
            po_requisition_obj = self.po_requisition_line.search(
                [('material_id', '=', line.id)])
            for i in po_requisition_obj:
                vals = {'product_id': line.id, 'product_uom': line.uom_id.id, 'price_unit': i.rate, 'product_qty':
                    i.current_req_qty, 'name': line.name, 'date_planned': datetime.now(), 'order_id': self.id, }
            data_lst.append((0, 0, vals))
        self.update({'order_line': data_lst})

        for order_lines in self.order_line:
            qty1 = 0
            specification = ''
            for po_requisition_line in self.po_requisition_line:
                if order_lines.product_id.id == po_requisition_line.material_id.id:
                    qty1 = qty1 + po_requisition_line.current_order_qty
                    if po_requisition_line.specification:
                        specification = specification + ' ' + \
                                        po_requisition_line.specification
            seller_price = self.get_seller_price(order_lines.product_id.id)
            received_qty = self.custom_compute_qty_received(
                order_lines.product_id.id)
            order_lines.update({'qty_received_custom': received_qty, 'price_unit': seller_price
                                   , 'product_qty': qty1, 'specification': str(specification)})

        if self.stage_id.approved == True:
            stage_master_obj = self.env['stage.master'].search(
                [('amend_and_draft', '=', True)])

    #             res = self.write({'stage_id': stage_master_obj.id, 'flag': False, 'state': 'draft'})

    """ called from Add Req. button of wizard-create PO Requisitions and Purchase order lines"""

    @api.depends('po_requisition_line', 'po_requisition_line.specification', 'po_requisition_line.current_req_qty')
    def compute_po_lines(self, purchase_order_id, project_wbs, project):
        purchase_order_id = self.env['purchase.order'].browse(
            self._context.get('active_id'))
        material_id_list = []
        rate = 0
        data_lst = []
        compressed_material_list = []
        material_estimate_obj = self.env['task.material.line']
        old_po_lines = [
            line.product_id.id for line in purchase_order_id.order_line]
        for line in purchase_order_id.po_requisition_line:
            material_id_list.append(line.material_id)
        compressed_material_list = set(material_id_list)
        for line in compressed_material_list:
            # Picking cost from Estimated Material/Wbs.
            project_wbs_obj = self.env['project.task'].search(
                [('name', '=', project_wbs.name), ('project_id', '=', project.id),
                 ('sub_project', '=', self.sub_project.id)])
            for wbs in project_wbs_obj:
                material_estimate_obj = wbs.material_estimate_line.search(
                    [('material_id', '=', line.id)], limit=1)

            vals = {
                'product_id': line.id,
                'product_uom': line.uom_id.id,
                'price_unit': material_estimate_obj.material_rate,
                'product_qty': 0,
                'name': line.name,
                'date_planned': datetime.now(),
                'order_id': purchase_order_id.id,
            }
            if line.id not in old_po_lines:
                res = self.env['purchase.order.line'].create(vals)

        # Merging the Quantity and specification of similar Products.
        for order_lines in self.order_line:
            # print("\n \n ======================>order_line as:::::::",order_lines)
            qty1 = 0
            specification = ''
            po_requisition_line = 0
            for po_requisition_line in purchase_order_id.po_requisition_line:
                # print("\n \n ---------po_reuisitions_line as--------",qty_received_custom)
                if order_lines.product_id.id == po_requisition_line.material_id.id:
                    qty1 = qty1 + po_requisition_line.current_order_qty
                    # print("\n \n ---------qty1 as--------",qty1)
                    if po_requisition_line.specification:
                        specification = specification + ' ' + \
                                        po_requisition_line.specification
            received_qty = order_lines.custom_compute_qty_received(
                order_lines.product_id.id)
            # print("\n @@@@@@@@@@@@@",type(received_qty))
            # print("received_qty[0]","\n\n",po_requisition_line.requisition_id.id,specification)
            # Comment @ Added this bcz type of received_qty is integer not list
            res = order_lines.write(
                {'qty_received_custom': received_qty, 'product_qty': qty1, 'order_id': purchase_order_id.id,
                 'requisition_id': po_requisition_line.requisition_id.id,
                 'specification': str(specification)})
            order_lines.qty_received_custom = received_qty
        # Pick the cost from product Master If vendor line is present in
        # product Master otherwise from estimation
        for line in purchase_order_id.order_line:
            product_obj = self.env['product.product'].search(
                [('id', '=', line.product_id.id)])
            seller_cost = line.price_unit
            for seller_id in product_obj.seller_ids:
                if seller_id.name.id == purchase_order_id.partner_id.id and seller_id.is_active == True:
                    seller_cost = seller_id.price
            received_qty = line.custom_compute_qty_received(product_obj.id)
            # print("PPPPPPPPPPPP\n",received_qty,type(received_qty))
            res = line.write(
                {'qty_received_custom': received_qty, 'price_unit': seller_cost, 'order_id': purchase_order_id.id,
                 'requisition_id': po_requisition_line.requisition_id.id})

    def change_state(self, context={}):
        # To check order line is not empty
        if not self.order_line:
            raise UserError(_('You Must select Product first !'))
        #         budget_obj = self.env['category.budget'].search(
        #             [('project_id', '=', self.project_id.id), ('project_wbs', '=', self.project_wbs.id)])
        #         for budget_line in budget_obj.category_line_ids:
        #             if budget_line.stage_id.approved == True:
        #                 total = 0
        #                 for po_line in self.po_requisition_line:
        #                     if po_line.task_id.category_id.id == budget_line.task_category.id:
        #                         total = (
        #                             po_line.rate * po_line.current_order_qty) + total
        #                 if total > ((budget_line.amount * budget_line.material_percent) / 100):
        #                     raise UserError(_('Insufficient Budget'))

        if context.get('copy') == True:
            self.state = 'shipment'
            self.flag = True
            # Validation of PO and bills with Budget
            budget_obj = self.env['category.budget'].search([('project_id', '=', self.project_id.id), (
                'sub_project', '=', self.sub_project.id), ('project_wbs', '=', self.project_wbs.id)])
            for budget_line in budget_obj.category_line_ids:
                if budget_line.stage_id.approved == True:
                    total = 0
                    for po_line in self.po_requisition_line:
                        if po_line.task_id.category_id.id == budget_line.task_category.id:
                            total = (
                                            po_line.rate * po_line.current_order_qty) + total
                    if total > budget_line.materialbudget_remaining:
                        raise UserError(_('Insufficient Budget'))
                    else:
                        budget_line.materialbudget_used = budget_line.materialbudget_used + \
                                                          total
            for line in self.po_requisition_line:
                if line.requisition_id.total_ordered_qty + line.current_order_qty <= line.requisition_id.current_req_qty:
                    line.requisition_id.total_ordered_qty = line.requisition_id.total_ordered_qty + \
                                                            line.current_order_qty
                else:
                    raise UserError(_('Sorry!! You cannot approve this PO'))

            # for line in self.order_line:
            #     line.wo_line_no = self.env['ir.sequence'].next_by_code(
            #         'purchase.order.line') or '/'

        else:
            flag = 0
            for purchase_line in self.order_line:
                if purchase_line.product_qty == 0:
                    flag = 1
                    break
                else:
                    flag = 0
            if flag:
                raise UserError(_("You haven't set processed quantities."))
            else:
                view_id = self.env.ref(
                    'pragtech_purchase.approval_wizard_form_view_purchase').id
                return {
                    'type': 'ir.actions.act_window',
                    'key2': 'client_action_multi',
                    'res_model': 'approval.wizard',
                    'multi': 'True',
                    'target': 'new',
                    'views': [[view_id, 'form']],
                }

    @api.model
    def _prepare_picking(self):
        # print("_prepare_picking==========================")
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'origin': self.name,
            'project_id': self.project_id.id,
            'project_wbs': self.project_wbs.id,
            'po_id': self.id,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
        }

    # This function is called on confirm shipment button
    def custom_create_picking(self):
        # print("custom_create_picking==========================")
        picking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                #                 old_picking = self.env['stock.picking'].search(
                #                     [('po_id', '=', self.id), ('state', '!=', 'done')])
                #                 if not old_picking:
                res = order._prepare_picking()
                picking = self.env['stock.picking'].create(res)
                #                 else:
                #                     picking = old_picking
                #                     picking.custome_action_cancel()
                moves = order.order_line.filtered(lambda r: r.product_id.type in [
                    'product', 'consu']).custom_create_stock_moves(picking)
        #                 move_ids = moves.action_confirm()
        #                 for move in move_ids:
        #                     moves = self.env['stock.move'].browse(move).id
        #                     moves.force_assign()
        return True

    # This function is called on cron
    def cron_custom_create_picking(self):
        picking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                #                 old_picking = self.env['stock.picking'].search(
                #                     [('po_id', '=', self.id), ('state', '!=', 'done')])
                #                 if not old_picking:
                res = order._prepare_picking()
                picking = self.env['stock.picking'].create(res)
                #                 else:
                #                     picking = old_picking
                #                     picking.custome_action_cancel()
                moves = order.order_line.filtered(lambda r: r.product_id.type in [
                    'product', 'consu']).cron_custom_create_stock_moves(picking)
                move_ids = moves.action_confirm()
                for move in move_ids:
                    moves = self.env['stock.move'].browse(move).id
                    moves.force_assign()
        return True

    # This function is called on confirm shipment button
    #     @api.multi
    #     def button_approve(self):
    #         self.custom_create_picking()
    #         for order_line in self.order_line:
    #             for schedule_line in order_line.delivery_schedule_line_ids:
    #                 if schedule_line.is_shipment_created == False:
    #                     return {}
    #         self.write({'state': 'purchase'})
    #
    #         return {}

    # This function is called on cron
    def cron_button_approve(self):
        self.cron_custom_create_picking()
        for order_line in self.order_line:
            if not order_line.delivery_schedule_line_ids and order_line.is_shipment_created == False:
                return {}
            for schedule_line in order_line.delivery_schedule_line_ids:
                if schedule_line.is_shipment_created == False:
                    return {}
        self.write({'state': 'purchase'})
        return {}

    def custom_create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            price_unit = line._get_stock_move_price_unit()
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'date': line.order_id.date_order,
                'date_expected': line.date_planned,
                'location_id': line.order_id.partner_id.property_stock_supplier.id,
                'location_dest_id': line.order_id._get_destination_location(),
                'picking_id': picking.id,
                'partner_id': line.order_id.dest_address_id.id,
                'move_dest_id': False,
                'state': 'draft',
                'purchase_line_id': line.id,
                'company_id': line.order_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': line.order_id.picking_type_id.id,
                'group_id': line.order_id.group_id.id,
                'procurement_id': False,
                'origin': line.order_id.name,
                'route_ids': line.order_id.picking_type_id.warehouse_id and [
                    (6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                'warehouse_id': line.order_id.picking_type_id.warehouse_id.id,
                'product_uom_qty': line.product_qty - line.qty_received
            }
            # Fullfill all related procurements with this po line
            diff_quantity = line.product_qty
            for procurement in line.procurement_ids:
                procurement_qty = procurement.product_uom._compute_qty_obj(
                    procurement.product_uom, procurement.product_qty, line.product_uom)
                tmp = template.copy()
                tmp.update({
                    'product_uom_qty': min(procurement_qty, diff_quantity),
                    'move_dest_id': procurement.move_dest_id.id,
                    'procurement_id': procurement.id,
                    'propagate': procurement.rule_id.propagate,
                })
                done += moves.create(tmp)
                diff_quantity -= min(procurement_qty, diff_quantity)
            if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                done += moves.create(template)
        return done

    @api.model
    def confirm_shipment_on_cron(self):
        po_objs = self.env['purchase.order'].search(
            [('state', '=', 'shipment')])
        for obj in po_objs:
            obj.cron_confirm_shipment()

    def cron_confirm_shipment(self):
        for order in self:
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step'
                        and order.amount_total < self.env.user.company_id.currency_id.compute(
                        order.company_id.po_double_validation_amount, order.currency_id)) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.cron_button_approve()
            else:
                order.write({'state': 'to approve'})
        return {}

    def button_confirm(self):
        # print("in default button_confirm")
        for order in self:
            if order.state not in ['draft', 'sent', 'shipment']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id.compute(
                        order.company_id.po_double_validation_amount, order.currency_id)) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    def confirm_shipment(self):
        # print("confirm_shipment==========================")
        for order in self:
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step'
                        and order.amount_total < self.env.user.company_id.currency_id.compute(
                        order.company_id.po_double_validation_amount, order.currency_id)) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return {}

    @api.onchange('requisition_ids')
    @api.depends('requisition_ids')
    def onchange_requisition_ids(self):
        data_lst = []
        if self.requisition_ids:
            for requisition in self.requisition_ids:
                purchase_line_obj = self.env['purchase.order.line'].search(
                    [('order_id.state', 'in', ['done', 'purchase']), ('requisition_id', '=', requisition.id)])
                if purchase_line_obj:
                    for purchase_line in purchase_line_obj:
                        qty = 0.0
                        qty += purchase_line.product_qty
                        available_qty = requisition.quantity - qty
                        data = {
                            'product_id': requisition.material_id.id,
                            'product_uom': requisition.unit.id,
                            'price_unit': requisition.rate,
                            'requisition_id': requisition.id,
                            'product_qty': available_qty,
                            'name': requisition.material_id.name,
                            'date_planned': datetime.now(),
                        }
                else:
                    data = {
                        'product_id': requisition.material_id.id,
                        'product_uom': requisition.unit.id,
                        'price_unit': requisition.rate,
                        'requisition_id': requisition.id,
                        'product_qty': requisition.quantity,
                        'name': requisition.material_id.name,
                        'date_planned': datetime.now(),
                    }
                data_lst.append((0, 0, data))
        self.update({'order_line': data_lst})

    @api.onchange('project_id')
    def onchange_project(self):
        self.project_wbs = self.sub_project = False
        # return required domain,ie.wbs of only selected project and materials
        # of selected Wbs
        project_wbs_lst = []
        project_ids = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id)])
        for i in project_ids:
            project_wbs_lst.append(i.name)
        sub_project_ids = []
        sub_project_obj = self.env['sub.project'].search(
            [('project_id', '=', self.project_id.id)])
        for line in sub_project_obj:
            sub_project_ids.append(line.id)
        # return {'domain': {'project_wbs': [('name', 'in',
        # project_wbs_lst)],'sub_project': [('id', 'in', sub_project_ids)]}}
        return {'domain': {'sub_project': [('id', 'in', sub_project_ids)]}}


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'

    currency_id = fields.Many2one('res.currency', 'Currency', readonly=False)
    brand_id = fields.Many2one('brand.brand')
    negotiated_rate = fields.Float('Negotiated Rate')
    credit_period = fields.Integer('Credit Period')
    requisition_id = fields.Many2one(
        'purchase.requisition', 'Requisition', readonly=True)
    group_id = fields.Many2one('project.task', 'Group')
    task_id = fields.Many2one('project.task', 'Task')
    task_category_id = fields.Many2one('task.category', related='task_id.category_id', store=True)
    requisition_date = fields.Date('Date')
    is_use = fields.Boolean('Use', Default=False)
    state = fields.Selection(related='order_id.state', store=True)
    specification = fields.Char('Specification', )
    qty_received_custom = fields.Float(
        'Received Qty', compute='_compute_qty_received', store=True)
    #     qty_invoiced_custom = fields.Float(compute='compute_qty_invoiced_custom', string="Billed Qty",store=True)
    total_rate = fields.Float(
        'Total Rate', help='This is rate of product including transportation and other charges',
        compute='get_landed_cost', store=True)
    delivery_schedule_line_ids = fields.One2many(
        'delivery.schedule', 'delivery_id', string='Delivery_Schedule_Line')
    is_shipment_created = fields.Boolean("Is Shipment Created", default=False)

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'qty_received', 'qty_received_custom',
                 'product_uom_qty', 'order_id.state')
    def _compute_qty_invoiced(self):
        for line in self:
            # compute qty_invoiced
            qty = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.move_id.state not in ['cancel']:
                    if inv_line.move_id.move_type == 'in_invoice':
                        qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                    elif inv_line.move_id.move_type == 'in_refund':
                        qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
            line.qty_invoiced = qty

            # compute qty_to_invoice
            if line.order_id.state in ['purchase', 'done']:
                if line.product_id.purchase_method == 'purchase':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    if line.requisition_id:
                        line.qty_to_invoice = line.qty_received_custom - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_received - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    # This function is called on confirm shipment button
    def custom_create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            price_unit = line._get_stock_move_price_unit()
            if not line.delivery_schedule_line_ids and line.is_shipment_created == False:
                template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'date': line.order_id.date_order,
                    'date_expected': line.date_planned,
                    'location_id': line.order_id.partner_id.property_stock_supplier.id,
                    'location_dest_id': line.order_id._get_destination_location(),
                    'picking_id': picking.id,
                    'partner_id': line.order_id.dest_address_id.id,
                    'move_dest_id': False,
                    'state': 'draft',
                    'purchase_line_id': line.id,
                    'company_id': line.order_id.company_id.id,
                    'price_unit': price_unit,
                    'picking_type_id': line.order_id.picking_type_id.id,
                    'group_id': line.order_id.group_id.id,
                    'procurement_id': False,
                    'origin': line.order_id.name,
                    'route_ids': line.order_id.picking_type_id.warehouse_id and [
                        (6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                    'warehouse_id': line.order_id.picking_type_id.warehouse_id.id,
                    'product_uom_qty': line.product_qty - line.qty_received
                }
                # Fullfill all related procurements with this po line
                diff_quantity = line.product_qty
                #                 for procurement in line.procurement_ids:
                #                     procurement_qty = procurement.product_uom._compute_qty_obj(
                #                         procurement.product_uom, procurement.product_qty, line.product_uom)
                #                     tmp = template.copy()
                #                     tmp.update({
                #                         'product_uom_qty': min(procurement_qty, diff_quantity),
                #                         'move_dest_id': procurement.move_dest_id.id,
                #                         'procurement_id': procurement.id,
                #                         'propagate': procurement.rule_id.propagate,
                #                     })
                #                     done += moves.create(tmp)
                #                     diff_quantity -= min(procurement_qty, diff_quantity)
                if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                    done += moves.create(template)
                line.is_shipment_created = True
        return done

    # This function is called on cron
    def cron_custom_create_stock_moves(self, picking):
        today = str(datetime.now().date())
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            for schedule_line in line.delivery_schedule_line_ids:
                if today == schedule_line.schedule_date and schedule_line.is_shipment_created == False:
                    price_unit = line._get_stock_move_price_unit()
                    template = {
                        'name': line.name or '',
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'date': line.order_id.date_order,
                        'date_expected': schedule_line.schedule_date,
                        'location_id': line.order_id.partner_id.property_stock_supplier.id,
                        'location_dest_id': line.order_id._get_destination_location(),
                        'picking_id': picking.id,
                        'partner_id': line.order_id.dest_address_id.id,
                        'move_dest_id': False,
                        'state': 'draft',
                        'purchase_line_id': line.id,
                        'company_id': line.order_id.company_id.id,
                        'price_unit': price_unit,
                        'picking_type_id': line.order_id.picking_type_id.id,
                        'group_id': line.order_id.group_id.id,
                        'procurement_id': False,
                        'origin': line.order_id.name,
                        'route_ids': line.order_id.picking_type_id.warehouse_id and [
                            (6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                        'warehouse_id': line.order_id.picking_type_id.warehouse_id.id,
                        # line.product_qty - line.qty_received
                        'product_uom_qty': schedule_line.quantity_to_deliver,
                    }
                    # Fullfill all related procurements with this po line
                    diff_quantity = line.product_qty
                    for procurement in line.procurement_ids:
                        procurement_qty = procurement.product_uom._compute_qty_obj(
                            procurement.product_uom, procurement.product_qty, line.product_uom)
                        tmp = template.copy()
                        tmp.update({
                            'product_uom_qty': min(procurement_qty, diff_quantity),
                            'move_dest_id': procurement.move_dest_id.id,
                            'procurement_id': procurement.id,
                            'propagate': procurement.rule_id.propagate,
                        })
                        done += moves.create(tmp)
                        diff_quantity -= min(procurement_qty, diff_quantity)
                    if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                        done += moves.create(template)
                    schedule_line.is_shipment_created = True
        return done

    @api.depends('price_subtotal', 'price_total', 'order_id.transport_amount', 'order_id.loading_charges',
                 'order_id.unloading_charges', 'order_id.other_charges')
    def get_landed_cost(self):
        for val in self:
            transport_amount = val.order_id.transport_amount + val.order_id.loading_charges + \
                               val.order_id.unloading_charges + val.order_id.other_charges
            if val.order_id.amount_total > 0:
                line_contribution = (
                                            transport_amount / val.order_id.amount_total) * val.price_total
                if val.product_qty > 0 and line_contribution > 0:
                    contribution_per_unit = line_contribution / val.product_qty
                    landed_rate = val.price_unit + contribution_per_unit
                    val.total_rate = landed_rate

    #     @api.onchange('order_id.picking_ids')
    #     @api.depends('order_id.invoice_ids','order_id.picking_ids','invoice_lines','product_id','invoice_lines.invoice_id.grn_ids')
    #     def compute_qty_invoiced_custom(self):
    #         billed_qty=0
    #         for this in self:
    # #             ##print "inside _compute_qty_invoiced========",this
    #     #         for line in self:
    #     #             ##print "line======",line,"line.invoice_lines=====",line.invoice_lines
    #     #             qty = 0.0
    #     #             for inv_line in line.invoice_lines:
    #     #                 ##print "inv_line========",inv_line
    #     #                 if inv_line.invoice_id.state not in ['cancel']:
    #     #                     qty += inv_line.uom_id._compute_quantity(inv_line.quantity, line.product_uom)
    #     #             line.qty_invoiced = qty
    #             picking_obj=this.env['stock.picking'].search([('origin','=',this.order_id.name)])
    #             for picking in picking_obj:
    #                 query="select invoice_id from picking_invoice_rel where picking_id={}".format(picking.id)
    #                 this.env.cr.execute(query)
    #                 invoice_id = this._cr.fetchall()
    #                 if invoice_id:
    #                     invoice_line=this.env['account.invoice.line'].search([('invoice_id','=',invoice_id),('product_id','=',this.product_id.id)])
    #                     vals={}
    #                     billed_qty=0
    #                     for line in invoice_line:
    #                         if this.order_id.name == line.invoice_id.origin:
    #                             billed_qty=billed_qty+line.quantity
    #             ##print "billed_qty--------",billed_qty,this,this.id
    #             if billed_qty>0:
    #                 query="update purchase_order_line set qty_invoiced={} where id={}".format(billed_qty,this.id)
    #                 this.env.cr.execute(query)
    #             ##print "billeddddddddddddddddddd Quantityyyyyyyyyyyy",billed_qty
    #             this.qty_invoiced_custom = billed_qty

    @api.depends('order_id.state', 'move_ids.state')
    def _compute_qty_received(self):
        for line in self:
            if line.order_id.state not in ['shipment', 'purchase', 'done']:
                line.qty_received = 0.0
                continue
            if line.product_id.type not in ['consu', 'product']:
                line.qty_received = line.product_qty
                continue
            total = 0.0
            for move in line.move_ids:
                if move.state == 'done':
                    if move.product_uom != line.product_uom:
                        total += move.product_uom._compute_quantity(
                            move.product_uom_qty, line.product_uom)
                    else:
                        total += move.product_uom_qty
            line.qty_received_custom = total

    @api.depends('order_id.state', 'move_ids.state')
    def custom_compute_qty_received(self, product_id):
        total = 0
        picking = self.env['stock.picking'].search(
            [('state', '=', 'done'), ('po_id', '=', self.order_id.id),
             ('partner_id', '=', self.order_id.partner_id.id)])
        for pickings in picking:
            for line in pickings.pack_operation_product_ids:
                if line.product_id.id == product_id:
                    total = total + line.qty_done
        # print("TOTAL",total,type(total))
        return total


class DeliverySchedule(models.Model):
    _name = 'delivery.schedule'
    _description = 'Delivery Schedule'

    delivery_id = fields.Many2one('purchase.order.line', string="Purchase")
    product_id = fields.Many2one(
        'product.product', string='Product', required=True)
    schedule_date = fields.Date("Schedule Delivery Date", required=True)
    quantity_to_deliver = fields.Integer("Quantity To Deliver", required=True)
    is_shipment_created = fields.Boolean(
        "Is Shipment Created", default=False, readonly=True)


# class RequisitionOrder(models.Model):
#     _name = 'requisition.order'
#     _inherit = ['mail.thread', 'ir.needaction_mixin']
#     _description = 'Requisition Order'
#
#     name = fields.Many2one('project.task', 'project WBS Name', required=True, domain=[
#                            ('is_wbs', '=', True), ('is_task', '=', False)])
#     project_id = fields.Many2one('project.project', 'Project', required=True)
#     task_category = fields.Many2many('task.category')
#     material_category = fields.Many2many('product.category')
#     material = fields.Many2one('product.product', 'Material')
#     group_id = fields.Many2one('project.task', 'Group')
#     task_id = fields.Many2one('project.task', 'Task')
#     order_line_id = fields.One2many(
#         'requisition.order.line', 'order_id', string='Requisition Order')
#     to_date = fields.Date(
#         'To Date', default=datetime.now() + timedelta(days=-30), required=True)
#     from_date = fields.Date(
#         'From Date', default=fields.date.today(), required=True)
#
#     _sql_constraints = [
#         ('name_uniq', 'unique(name)', 'Wbs Name must be unique!'),
#     ]
#
#     @api.multi
#     def compute_tree_labour(self):
#         return {
#             'name': _('labour tree'),
#             'context': self._context,
#             'view_type': 'tree',
#             'view_mode': 'tree',
#             'res_model': 'labour.master',
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#             'domain': [('parent_labour_id', '=', False), ('parent_group_id', '=', False)],
#         }
#
#     @api.multi
#     @api.depends('project_id', 'name', 'group_id', 'task_category', 'task_id', 'material_category', 'material')
#     def compute_requisitions_lines(self):
#         # Search from different fields and add requisition depending on search
#         # result
#         requisition_list = []
#         project_task_obj = self.env['project.task'].search(
#             [('project_id', '=', self.project_id.id), ('name', '=', self.name.name), ('sub_project', '=', self.sub_project.id)])
#         domain = []
#         task_category = []
#         material_category = []
#         domain.append(('project_wbs_id', '=', project_task_obj.id))
#         domain.append(('date_start', '>=', self.from_date))
#         domain.append(('date_start', '<=', self.to_date))
#         if self.group_id:
#             domain.append(('group_ids', '=', self.group_id.id))
#         if self.task_id:
#             domain.append(('task_id', '=', self.task_id.id))
#         if self.task_id:
#             domain.append(('task_id', '=', self.task_id.id))
#
#         if self.task_category:
#             for i in self.task_category:
#                 task_category.append(i.id)
#             domain.append(('task_category', 'in', task_category))
#
#         if self.material_category:
#             for i in self.material_category:
#                 material_category.append(i.id)
#             domain.append(('material_category', 'in', material_category))
#
#         material_estimate_obj = self.env['material.estimate'].search(domain)
#         st_id = self.env['transaction.stage'].search(
#             [('draft', '=', True), ('model', '=', 'requisition.order.line')])
#         req_no = 0
#         for line in material_estimate_obj:
#             req_no += 1
#             vals = {
#                 'material_id': line.name.id,
#                 'quantity': line.quantity,
#                 'unit': line.unit_name,
#                 'rate': line.rate,
#                 'task_id': line.task_id.id,
#                 'group_id': line.group_ids.id,
#                 'name': str(self.name.name) + '-Req' + str(req_no),
#                 'requisition_date': datetime.now(),
#             }
#             requisition_list.append((0, 0, vals))
#         self.update({'order_line_id': requisition_list})
#         return {
#             'context': self.env.context,
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'requisition.order',
#             'res_id': self.id,
#             'view_id': False,
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#         }
#
#     @api.depends('project_id', 'name', 'group_id', 'task_category')
#     @api.onchange('project_id', 'name', 'group_id', 'task_category')
#     def all_onchange(self):
#         project_lst = []
#         name_lst = []
#         if self.project_id:
#             project_ids = self.env['project.task'].search(
#                 [('project_id', '=', self.project_id.id)])
#             for i in project_ids:
#                 project_lst.append(i.name)
#         if self.name:
#             project_ids = self.env['material.estimate'].search(
#                 [('project_wbs_id', '=', self.name.id)])
#             for i in project_ids:
#                 name_lst.append(i.group_ids.id)
#
#         return {'domain': {'name': [('name', 'in', project_lst)], 'group_id': [('id', 'in', name_lst)],
#                            'task_id': [('parent_id', '=', self.group_id.id)]}}
#
#
# class RequisitionOrderLine(models.Model):
#     _name = 'requisition.order.line'
#     _inherit = ['mail.thread', 'ir.needaction_mixin']
#     _description = 'Requisition Order Line'
#
#     @api.multi
#     def change_state(self, context):
#         view_id = self.env.ref(
#             'pragtech_purchase.approval_wizard_form_view_purchase').id
#         return {
#
#             'type': 'ir.actions.act_window',
#             'key2': 'client_action_multi',
#             'res_model': 'approval.wizard',
#             'multi': 'True',
#             'target': 'new',
#             'views': [[view_id, 'form']],
#         }
#
#     name = fields.Char('Requisition No')
#     group_id = fields.Many2one('project.task', 'Group')
#     task_id = fields.Many2one('project.task', 'Task')
#     flag = fields.Boolean('Flag', default=False)
#     material_id = fields.Many2one('product.product', 'Material')
#     requisition_date = fields.Date(
#         'Date', default=fields.date.today(), required=True)
#     requirement_date = fields.Date('Requirement Date')
#     procurement_date = fields.Date('Procurement Date')
#     quantity = fields.Integer('Wbs Quantity')
#     specification = fields.Char('Specification')
#     remark = fields.Char('Remark')
#     total_approved_qty = fields.Float('Approved Qty', readonly=True)
#     requisition_qty = fields.Float('Requisition Qty')
#     total_ordered_qty = fields.Float('Ordered Qty', readonly=True)
#     balance_qty = fields.Float('Balance Qty')
#     status = fields.Selection(
#         [('active', 'Active'), ('inactive', 'Inactive')], 'Status')
#     priority = fields.Selection([('high', 'High'), ('low', 'Low')], 'Priority')
#     brand_id = fields.Many2one('brand.brand', 'Brand')
#     requisition_type = fields.Selection(
#         [('estimated', 'Estimated'), ('non_estimated', 'Non Estimated')], 'Type')
#     order_id = fields.Many2one('requisition.order', 'order_line_id')
#     unit = fields.Many2one('product.uom', 'UOM', required=True)
#     rate = fields.Float('Rate')
#     procurement_type = fields.Selection([('New Purchase from Supplier', 'New Purchase from Supplier'),
#                                          ('Cash Purchase ', 'Cash Purchase '),
#                                          ('IST from other sites', 'IST from other sites'), ], 'Procurement Type')
#     warehouse_id = fields.Char('Procurement Type', readonly=True)
#     requisition_fulfill = fields.Boolean('Req fulfill')
#     stage_id = fields.Many2one(
#         'transaction.stage', domain=[('model', '=', 'requisition.order.line')])
#
#     project_wbs = fields.Many2one(
#         'project.task', related='order_id.name', store=True)
#     project_id = fields.Many2one(
#         'project.project', related='order_id.project_id', store=True)
#     material_category = fields.Many2many(
#         'product.category', related='order_id.material_category', store=True)
#
#     @api.multi
#     @api.onchange('stage_id')
#     @api.depends('stage_id.approved')
#     def onchange_stage(self):
#         if self.stage_id.approved:
#             self.flag = True


class MaterialRate(models.Model):
    _name = 'material.rate'
    _description = 'Material Rate'

    name = fields.Char('Name', required=True)


class POMaterialRate(models.Model):
    _name = 'po.material.rate'
    _description = 'PO Material Rate'

    material_id = fields.Many2one('product.product', 'Material')
    rate_master_id = fields.Many2one(
        'material.rate', string='Rate master', required=True)
    material_rate_lines = fields.One2many(
        'po.material.rate.line', 'material_rate_id')


class POMaterialRateLine(models.Model):
    _name = 'po.material.rate.line'
    _description = 'PO Material Rate Line'

    supplier_id = fields.Many2one('res.partner', 'Supplier', required=True)
    name = fields.Many2one('product.product', 'Material', required=True)
    material_rate_id = fields.Many2one('po.material.rate')
    rate = fields.Float('Rate', required=True)
    discount = fields.Float('Discount(%)')
    credit_period = fields.Float('Credit Period')
    net_rate = fields.Float(
        compute='_compute_amount', string='Net Rate', readonly=True, store=True)
    conversion_factor = fields.Float('Conversion Factor', default='1')
    unit_commercial = fields.Many2one('uom.uom', required=True)
    tax_id = fields.Many2many(
        'account.tax', 'po_material_rate_line_tax_rel', 'tax_id', 'rate_line_id', string='Taxes')
    brand_id = fields.Many2one('brand.brand', 'Brand')
    valid_till = fields.Datetime('Valid Till')
    currency_id = fields.Many2one('res.currency', 'Currency')
    currency_convfact = fields.Float('Currency Conversion Factor')
    currency_rate = fields.Float('Currency Rate')
    transportation_charges = fields.Float('Transportation Charges')
    loading_charges = fields.Float('Loading Charges')
    unloading_charges = fields.Float('Unloading Charges')
    installation_charges = fields.Float('Installation Charges')
    any_other_charges = fields.Float('Any Other Charges')
    ref_no = fields.Char('Reference Number')
    approve_date = fields.Date('Approve Date')

    @api.onchange('name')
    def onchange_name(self):
        journals = self.env['conversion.uom'].search(
            [('prod_uom_id', '=', self.name.id)])
        vals = []
        for i in journals:
            vals.append(i.from_uom_id.id)
            vals.append(i.to_uom_id.id)
        return {'domain': {'unit_commercial': [('id', 'in', vals)], 'brand_id': [('material_id', '=', self.name.id)]}}

    @api.onchange('supplier_id')
    def onchange_supplier_id(self):
        partner = self.env['res.partner'].search(
            [('name', '=', self.supplier_id.name)])
        vals = []
        for i in partner:
            vals.append(i.property_purchase_currency_id.id)
        return {'domain': {'currency_id': [('id', 'in', vals)]}}

    @api.depends('conversion_factor', 'discount', 'rate', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.rate * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price, line.currency_id, quantity=1.0, product=line.name, partner=line.supplier_id)
            line.update({
                'net_rate': taxes['total_included'],
            })


class TransactionStage(models.Model):
    _name = 'transaction.stage'
    _description = 'Transaction Stage'

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1)
    draft = fields.Boolean('Drafts')
    approved = fields.Boolean('Approved')
    model = fields.Many2one('ir.model')


class PO_Requisition(models.Model):
    _name = 'po.requisition'
    _description = 'PO Requisition'

    group_id = fields.Many2one('project.task', 'Task Group')
    task_id = fields.Many2one('project.task', 'Task')
    material_id = fields.Many2one('product.product', 'Material')
    quantity = fields.Integer('Estimated Quantity')
    specification = fields.Char('Specification')
    remark = fields.Char('Remark')
    estimated_qty = fields.Float('Estimated Qty')
    Requisition_as_on_date = fields.Float('Requisition as on date')
    current_req_qty = fields.Float('Current requisition Qty', readonly=False)
    unit = fields.Many2one('uom.uom', 'UOM', required=True)
    rate = fields.Float('Rate')
    warehouse_id = fields.Char('Procurement Type', readonly=True)
    stage_id = fields.Many2one(
        'transaction.stage', domain=[('model', '=', 'requisition.order.line')], copy=False)
    project_wbs = fields.Many2one('project.task', 'Project Wbs')
    project_id = fields.Many2one('project.project', 'Project')

    sub_project = fields.Many2one('sub.project', 'Sub Project')

    material_category = fields.Many2one(
        'product.category', 'Material Category')
    task_category = fields.Many2one('task.category', 'Task Category', related='task_id.category_id', store=True)
    me_sequence = fields.Char(readonly=True)
    requisition_id = fields.Many2one('purchase.requisition', 'Requisition')
    order_id = fields.Many2one('purchase.order')
    total_ordered_qty = fields.Float('Ordered Qty')
    requisition_qty = fields.Float('Requisition Qty')
    current_order_qty = fields.Float('Current Order Qty')
    is_red = fields.Boolean()

    def write(self, vals):
        res = super(PO_Requisition, self).write(vals)
        return res

    def unlink(self):
        if self.order_id.state == 'shipment' or self.order_id.state == 'purchase' or self.order_id.state == 'done':
            raise UserError(
                ('Cannot delete requisition line which is in shipment state'))
        else:
            return super(PO_Requisition, self).unlink()

    @api.onchange('current_order_qty')
    def onchnge_order_qty(self):
        if self.current_order_qty > self.requisition_qty - self.total_ordered_qty:
            raise UserError(
                _('Order quantity must be less than requisition quantity'))


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'
    _order = "create_date"
    _description = 'Product Supplier Info'

    is_active = fields.Boolean('Active')
    date = fields.Datetime('Date', default=datetime.now())
