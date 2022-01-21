from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ApprovalWizard(models.TransientModel):
    _name = 'approval.wizard'
    _description = 'Approval Wizard'
    _inherit = ['mail.thread']

    module = model = fields.Many2one('ir.model', 'Transaction')
    current_stage = fields.Many2one('stage.master', 'Current Stage', readonly=True)
    new_stage = fields.Many2one('stage.master', 'New Stage')
    remark = fields.Text('Remark', required=True)
    current_stage_seq = fields.Integer('Sequence')
    new_stage_domain = fields.Char('New Stage Domain', help='Internal use only to set domain for new_stage')

#     @api.model
#     def default_get(self, fields):
#         compressed_list = []
#         stage_list = []
#         res = super(ApprovalWizard, self).default_get(fields)
#         context = dict(self._context or {})
#         active_model = context.get('active_model')
#         active_ids = context.get('active_ids')
#         model_rec = self.env[active_model].browse(active_ids)
#         for record in model_rec:
#             model_id = self.env['ir.model'].search([('model', '=', active_model)])
#             stage_list.append(record.stage_id.id)
#             res.update({
#                 'current_stage': record.stage_id.id,
#                 'module': model_id.id,
#             })
#         compressed_list = set(stage_list)
#         if len(compressed_list) > 1:
#             raise UserError(_('Please select records having same stage'))
#         return res

    @api.model
    def default_get(self, fields):
        ##print "fields ssssssssss-----",fields
        compressed_list = []
        stage_list = []
        res = super(ApprovalWizard, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
#         ##print "active_model--------",active_model
        if active_model=='project.task':
            active_ids = context.get('active_ids')
            model_rec = self.env[active_model].browse(active_ids)
            for record in model_rec:
                model_id = self.env['ir.model'].search([('model', '=', active_model)])
#                 ##print "model_id--------",model_id
                stage_list.append(record.stage_master_id.id)
                res.update({
                    'current_stage': record.stage_master_id.id,
                    'module': model_id.id,
                })
            ##print "res from task---------------",res
            compressed_list = set(stage_list)
        else :
            active_ids = context.get('active_ids')
            model_rec = self.env[active_model].browse(active_ids)
            for record in model_rec:
                model_id = self.env['ir.model'].search([('model', '=', active_model)])
#                 ##print "model_id--------",model_id
                stage_list.append(record.stage_id.id)
                res.update({
                    'current_stage': record.stage_id.id,
                    'module': model_id.id,
                })
            ##print "res-----------",res
            compressed_list = set(stage_list)
        if len(compressed_list) > 1:
            raise UserError(_('Please select records having same stage'))
        return res
    
    def get_stagetransaction_record(self,from_stage,model):
        user_obj = self.env['res.users']
        user_data = user_obj.browse(self._uid)
        user_groups = user_data.groups_id
        #print user_groups
        for user in user_groups :
            #print user
            stage_obj = self.env['stage.transaction'].search([('from_stage', '=', from_stage), ('model', '=', model)])#, ('groups', '=', user.id)
            if stage_obj:
                ##print "=====================>>>>",stage_obj
                return stage_obj
    
    
    @api.onchange('current_stage')
    def onchange_current_stage(self):
        ##print "onchange_current_stage-----------------",self
        context = dict(self._context or {})
        result = {}
        active_model = context.get('active_model')
        stage_obj = self.env['stage.transaction']
        if active_model=='project.task':
            ##print "active_model---",active_model
            active_ids = context.get('active_ids')
            model_rec = self.env[active_model].browse(active_ids)
            for record in model_rec:
                model_id = self.env['ir.model'].search([('model', '=', active_model)])
                ##print "model_id--------",model_id
                stage_obj = self.get_stagetransaction_record(record.stage_master_id.id,model_id.id) or ""
                ##print "stage_obj------------",stage_obj
                stage_domain = [stage.to_stage.id for stage in stage_obj]
        else:
            active_model = context.get('active_model')
            ##print "active_model---",active_model
            active_ids = context.get('active_ids')
            model_rec = self.env[active_model].browse(active_ids)
            for record in model_rec:
                model_id = self.env['ir.model'].search([('model', '=', active_model)])
                ##print "model_id--------",model_id
                stage_obj = self.get_stagetransaction_record(record.stage_id.id,model_id.id) or ""
                ##print "stage_obj------------",stage_obj
                stage_domain = [stage.to_stage.id for stage in stage_obj]
        ##print "stage_domain------------",stage_domain
        return {'domain': {'new_stage': [('id', 'in', stage_domain)]}}
#     
#     @api.onchange('current_stage')
#     def onchange_current_stage(self):
#         ##print "onchange_current_stage ppc-----------------",self
#         context = dict(self._context or {})
#         result = {}
#         group=""
#         active_model = context.get('active_model')
#         ##print "active_model---",active_model
#         active_ids = context.get('active_ids')
#         model_rec = self.env[active_model].browse(active_ids)
#         for record in model_rec:
#             model_id = self.env['ir.model'].search([('model', '=', active_model)])
#             ##print "model_id--------",model_id
#             stage_obj = self.get_stagetransaction_record(record.stage_id.id,model_id.id) or ""
#             ##print "stage_obj------------",stage_obj
#             stage_domain = [stage.to_stage.id for stage in stage_obj]
#         ##print "stage_domain------------",stage_domain
#         return {'domain': {'new_stage': [('id', 'in', stage_domain)]}}

    
    def update_status(self):
        app_list = []
        data_lst = []
        context = dict(self._context or {})
        self.with_context(aprv=True)
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        app = self.env[active_model].browse(active_ids)
        if self.current_stage and self.new_stage:
            for approval in app:
                if self.new_stage.approved:
                    if active_model == 'project.task':
                        approval.stage_master_id = self.new_stage
                    else:
                        approval.stage_id = self.new_stage

                    vals = {
                        'date': datetime.now(),
                        'from_stage': self.current_stage.id,
                        'to_stage': self.new_stage.id,
                        'remark': self.remark,
                        'res_id': approval.id,
                        'model': active_model,
                    }
                    context.update({'copy': True})
                    approval.change_state(context)
                else:
                    if active_model=='project.task':
                        approval.stage_master_id = self.new_stage
                    else:
                        approval.stage_id = self.new_stage
                    approval.remark = self.remark
                    vals = {
                        'date': datetime.now(),
                        'from_stage': self.current_stage.id,
                        'to_stage': self.new_stage.id,
                        'remark': self.remark,
                        'res_id': approval.id,
                        'model': active_model,
                    }
                    context.update({'copy': False})
                    approval.change_state(context)
                self.env['mail.messages'].create(vals)
        else:
            raise UserError(("Please select new_stage for transaction."))

    
    def reset_status(self):
        context = dict(self._context or {})
        stage_obj = self.env['stage.master'].search([('draft', '=', True)])
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        app = self.env[active_model].browse(active_ids)
        for approval in app:
            approval.stage_id = stage_obj.id
            vals = {
                'date': datetime.now(),
                'from_stage': self.current_stage.id,
                'to_stage': stage_obj.id,
                'remark': self.remark,
                'res_id': approval.id,
                'model': active_model,
            }
            self.env['mail.messages'].create(vals)
