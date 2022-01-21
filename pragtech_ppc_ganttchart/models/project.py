from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
import datetime
from odoo.http import request


    
    
class ProjectProject(models.Model):
    _inherit = 'project.project'
    _description = 'Project'
    
    @api.multi
    def open_gantt_view_action1(self):
        request.params['session_pr_id'] = self.id
        request.session['project_id_wizard'] = self.id
        
        return {
            'name':'Gantt Chart',
            'type': 'ir.actions.client',
            'tag':'gantt_chart',
            'params': {'project_id':self.id},
            'context':{'project_id':self.id},
        }

