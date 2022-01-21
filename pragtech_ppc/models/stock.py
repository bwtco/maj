from odoo import fields, models


#
# class stock_picking(models.Model):
#     _inherit = 'stock.picking'
#     _description = 'Stock Picking'
#     
# 
#     def custome_action_cancel(self, cr, uid, ids, context=None):
#         for pick in self.browse(cr, uid, ids, context=context):
#             ids2 = [move.id for move in pick.move_lines]
#             self.pool.get('stock.move').action_cancel(cr, uid, ids2, context)
#             objs=self.pool.get('stock.move').browse(cr,uid,ids2)
#             for i in objs:
#                 i.unlink()
#         return True
# 
# 
#     @api.model
#     def _default_stage(self):
#         st_id = self.env['stage.master'].search([('draft', '=', True)])
#         if st_id:
#             return st_id.id
# 
#     
#     def change_state(self, context):
#         if context.get('copy') == True:
#             self.flag = True
#         else:
#             flag = 0
#             flag1 = 0
#             for picking_line in self.pack_operation_product_ids:
#                 if picking_line.qty_done == 0:
#                     flag = 1
#                     break
#                 elif picking_line.product_qty < picking_line.qty_done:
#                     flag1 = 1
#                     break
#                 else:
#                     flag = 0
#                     flag1 = 0
#             if flag:
#                 raise UserError(_("You haven't set processed quantities."))
#             if flag1:
#                 raise UserError(_("product quantity exceed from related purchase order."))
#             else:
#                 view_id = self.env.ref('pragtech_ppc.approval_wizard_form_view').id
#                 return {
# 
#                     'type': 'ir.actions.act_window',
#                     'key2': 'client_action_multi',
#                     'res_model': 'approval.wizard',
#                     'multi': 'True',
#                     'target': 'new',
#                     'views': [[view_id, 'form']],
#                 }
# 
# 
#     project_wbs = fields.Many2one('project.task', 'Sub project', domain=[('is_wbs', '=', True), ('is_task', '=', False)], readonly=True)
#     project_id = fields.Many2one('project.project', 'Project', readonly=True)
# 
#     sub_project = fields.Many2one('sub.project', 'Sub Project')
# 
#     type = fields.Selection([('from_supplier', 'Receipt from Supplier'), ('from_other_site', 'Receipt from Other site')], 'Type', readonly=True)
#     invoice_no = fields.Char('Invoice No')
#     invoice_date = fields.Datetime('Invoice Date')
#     challan_no = fields.Char('Delivery Challan No')
#     bill_id = fields.Char('Bill')
#     stage_id = fields.Many2one('stage.master', 'Stage', default=_default_stage, readonly=True)
#     brand_id = fields.Many2one('brand.brand', 'Brand')
#     vehicle_no = fields.Char('Vehicle No')
#     transport_bill_id = fields.Char('Transport Bill')
#     transport_amount = fields.Float('Transport Amount')
#     loading_charges = fields.Float('Loading Charges')
#     other_charges = fields.Float('Other Charges')
#     other_charges2 = fields.Float('Other Charges2')
#     gate_registration_no = fields.Char('Gate Registration No')
#     gate_registration_date = fields.Datetime('Gate Registration Date')
#     challan_date = fields.Datetime('Challan Date')
#     challan_qty = fields.Integer('Challan Qty')
#     flag = fields.Boolean('Flag', default=False)
#     po_id = fields.Many2one('purchase.order', string='PO', readonly=True)
#     mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage', domain=lambda self: [('model', '=', self._name)], auto_join=True,
#                                 readonly=True)
# 
#     def _create_backorder(self, cr, uid, picking, backorder_moves=[], context=None):
#         """ Move all non-done lines into a new backorder picking. If the key 'do_only_split' is given in the context, then move all lines not in context.get('split', []) instead of all non-done lines.
#         """
#         if not backorder_moves:
#             backorder_moves = picking.move_lines
#         backorder_move_ids = [x.id for x in backorder_moves if x.state not in ('done', 'cancel')]
#         if 'do_only_split' in context and context['do_only_split']:
#             backorder_move_ids = [x.id for x in backorder_moves if x.id not in context.get('split', [])]
# 
#         if backorder_move_ids:
#             backorder_id = self.copy(cr, uid, picking.id, {
#                 'name': '/',
#                 'move_lines': [],
#                 'pack_operation_ids': [],
#                 'backorder_id': picking.id,
#             })
#             backorder = self.browse(cr, uid, backorder_id, context=context)
#             self.message_post(cr, uid, picking.id, body=_("Back order <em>%s</em> <b>created</b>.") % (backorder.name), context=context)
#             move_obj = self.pool.get("stock.move")
#             move_obj.write(cr, uid, backorder_move_ids, {'picking_id': backorder_id}, context=context)
# 
#             if not picking.date_done:
#                 self.write(cr, uid, [picking.id], {'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
#             self.action_confirm(cr, uid, [backorder_id], context=context)
#             self.action_assign(cr, uid, [backorder_id], context=context)
#             stage_obj = self.pool.get('stage.master').search(cr, uid, [('draft', '=', True)])[0]
#             pick = self.pool.get('stock.picking')
#             pick_obj = pick.browse(cr, uid, backorder_id)
#             pick_obj.flag = False
#             pick_obj.stage_id = stage_obj
#             return backorder_id
#         return False
# 
#     def action_cancel(self, cr, uid, ids, context=None):
#         existing_stage = []
#         po_obj = self.pool.get('purchase.order')
#         stage_obj = self.pool.get('stage.master')
#         po_req = self.pool.get('purchase.requisition')
#         mail_message = self.pool.get('mail.messages')
#         for picking in self.browse(cr, uid, ids):
#             po_ids = po_obj.search(cr, uid, [('id', '=', picking.po_id.id)])
#             po_rec = po_obj.browse(cr, uid, po_ids[0])
#             st_id = stage_obj.search(cr, uid, [('approved', '=', True)])
#             st_id_draft = stage_obj.search(cr, uid, [('draft', '=', True)])
#             for picking_line in picking.pack_operation_product_ids:
#                 po_req_ids = self.pool.get('po.requisition').search(cr, uid,
#                                                                     [('order_id', '=', po_rec.id), ('material_id', '=', picking_line.product_id.id)])
#                 purchase_requi = self.pool.get('po.requisition').browse(cr, uid, po_req_ids[0])
#                 purchase_line = self.pool.get('purchase.order.line').search(cr, uid, [('order_id', '=', po_rec.id),
#                                                                                       ('product_id', '=', picking_line.product_id.id)])
#                 purchase_line_obj = self.pool.get('purchase.order.line').browse(cr, uid, purchase_line[0])
#                 req_ids = po_req.search(cr, uid,
#                                         [('name', '=', purchase_requi.requisition_id.name), ('material_id', '=', purchase_requi.material_id.id)])
#                 requisition = po_req.browse(cr, uid, req_ids[0])
#                 vals = {
#                     'project_id': requisition.project_id.id,
#                     'project_wbs': requisition.project_wbs.id,
#                     'rate': purchase_line_obj.price_unit,
#                     'unit': picking_line.product_uom_id.id,
#                     'current_req_qty': picking_line.product_qty,
#                     'material_id': picking_line.product_id.id,
#                     'stage_id': st_id[0],
#                     'specification': 'Release from' + ' ' + po_rec.name
#                 }
#                 requisition_id = po_req.create(cr, uid, vals)
#                 msg_ids = {
#                     'date': datetime.now(),
#                     'from_stage': st_id_draft[0],
#                     'to_stage': st_id[0],
#                     'remark': None,
#                     'model': 'purchase.requisition',
#                     'res_id': requisition_id
#                 }
#                 mail_message.create(cr, uid, msg_ids)
#                 backorder_pick_ids = self.search(cr, uid, [('id', '=', picking.backorder_id.id)])
#                 stage_id = stage_obj.search(cr, uid, [('foreclosed', '=', True)])
#                 self.write(cr, uid, backorder_pick_ids, {'stage_id': stage_id[0]})
#         return super(stock_picking, self).action_cancel(cr, uid, ids, context)
# 
# 
# class stock_pack_operation(models.Model):
#     _inherit = 'stock.pack.operation'
#     _description = 'Stock Pack Operation'
# 
#     specification = fields.Char('Specification')
#     total_rate = fields.Char('Rate')
#     retained_quantity = fields.Integer('Retained Quantity')
#     rejected_quantity = fields.Integer('Rejected Quantity')
# 
# 
class stock_move(models.Model):
    _inherit = 'stock.move'
    _description = 'Stock Move'
    task_category = fields.Many2one('task.category', 'Task Category')


class stock_location(models.Model):
    _inherit = 'stock.location'
    _description = 'Stock Location'

    project_id = fields.Many2one('project.project', 'Project')
