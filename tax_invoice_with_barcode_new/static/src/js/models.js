/* Copyright 2018 Tecnativa - David Vidal
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

odoo.define('tax_invoice_with_barcode_new.models_inherit', function (require) {
    'use strict';

    var models = require('point_of_sale.models');

    var order_super = models.Order.prototype;

    models.PosModel = models.PosModel.extend({
        push_and_invoice_order: function (order) {
            console.log("push_and_invoice_order");
            var self = this;
            var invoiced = new Promise(function (resolveInvoiced, rejectInvoiced) {
                if(!order.get_client()){
                    rejectInvoiced({code:400, message:'Missing Customer', data:{}});
                }
                else {
                    var order_id = self.db.add_order(order.export_as_JSON());

                    self.flush_mutex.exec(function () {
                        var done =  new Promise(function (resolveDone, rejectDone) {
                            // send the order to the server
                            // we have a 30 seconds timeout on this push.
                            // FIXME: if the server takes more than 30 seconds to accept the order,
                            // the client will believe it wasn't successfully sent, and very bad
                            // things will happen as a duplicate will be sent next time
                            // so we must make sure the server detects and ignores duplicated orders

                            var transfer = self._flush_orders([self.db.get_order(order_id)], {timeout:30000, to_invoice:true});

                            transfer.catch(function (error) {
                                rejectInvoiced(error);
                                rejectDone();
                            });

                            // on success, get the order id generated by the server
                            transfer.then(function(order_server_id){
                                // generate the pdf and download it
                                if (order_server_id.length && !order.is_to_email()) {
                                    self.chrome.do_action('tax_invoice_with_barcode_new.tax_barcode_account_invoices',{additional_context:{
                                        active_ids:order_server_id,
                                    }}).then(function () {
                                        resolveInvoiced(order_server_id);
                                        resolveDone();
                                    }).guardedCatch(function (error) {
                                        rejectInvoiced({code:401, message:'Backend Invoice', data:{order: order}});
                                        rejectDone();
                                    });
                                } else if (order_server_id.length) {
                                    resolveInvoiced(order_server_id);
                                    resolveDone();
                                } else {
                                    // The order has been pushed separately in batch when
                                    // the connection came back.
                                    // The user has to go to the backend to print the invoice
                                    rejectInvoiced({code:401, message:'Backend Invoice', data:{order: order}});
                                    rejectDone();
                                }
                            });
                            return done;
                        });
                    });
                }
            });

            return invoiced;
        },
    });
});
