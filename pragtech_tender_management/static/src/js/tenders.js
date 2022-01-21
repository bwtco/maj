odoo.define('pragtech_tender_management.tenders', function (require) {
    $(document).ready(function(){
         $('.material_input_amount').css('display','none')
         $('.labour_input_amount').css('display','none')
         $('.overhead_input_amount').css('display','none')
         $('.total_input_amount').css('display','none')

         $('input[class=material_your_price]').change(function(event)
         {
            if(event && event.currentTarget && event.currentTarget.attributes && event.currentTarget.attributes.my_id)
            {
                var id = event.currentTarget.attributes.my_id.value
//                console.log('id==========',id)
                var a = ''
                var b = ''
                var qty = '#material_quantity-'+id+' span'
                var price = 'input[name=material_your_price-'+id+']'
                var mat_amt = '#material_amount-'+id+' span'
                 var total = '#total_amount'
                 var total_amount_duplicate = '#total_amount_duplicate'
                 var material_amount_duplicate = 'material_amount_duplicate-'+id
                 var labour_amount_duplicate = 'labour_amount_duplicate-'+id
                 var overhead_amount_duplicate = 'overhead_amount_duplicate-'+id
//                 console.log('material_amount_duplicate',material_amount_duplicate)
//                 console.log('labour_amount_duplicate',labour_amount_duplicate)
//                 console.log('overhead_amount_duplicate',overhead_amount_duplicate)
//                console.log('*************',$(material_amount_duplicate))
//                console.log($(price))
//                console.log($(mat_amt))
//                console.log("$(qty).text():::",$(qty).text())
//                console.log("$(qty).text(2)22222222 :::",typeof $(qty).text())
//                console.log("$(qty).text()333:::",typeof Number($(qty).text()))
//                console.log("$(price)[0].value:::",$(price)[0].value)
//                console.log("2222222222",typeof $(price)[0].value)
//                console.log("33333333333333 ",typeof Number($(price)[0].value))

                a = $(qty).text()
                b = $(price)[0].value

                var aa = a.replace(/[^0-9.-]+/g,"");
                var aValue = parseFloat(aa)
//                console.log("aValue",aValue)

                var bb = b.replace(/[^0-9.-]+/g,"");
                var bValue = parseFloat(bb)
//                console.log("bValue",bValue)

                var material_amount = aValue * bValue
//                console.log("material_amount",material_amount)
//                console.log("$(material_amount)",$(material_amount))


                var mat_amt1 = $('#material_amount-'+id+' span').text(material_amount)
                $('[name="' + material_amount_duplicate + '"]').val(material_amount)
//                console.log('mat_amt1',$(mat_amt1))
//                console.log('material_amount_duplicate',$(mat_amt1_duplicate))
//                console.log("material_input_amount amt==========",$('.material_input_amount').val())
                var mat_all = $('.material_amount')
                var lab_all = $('.labour_amount')
                var overhead_all = $('.overhead_amount')
                var all_tot = 0.00
//                console.log('22222222222222222',mat_all)
                for(var i=0;i<mat_all.length;i++)
                {
                    all_tot += Number(mat_all[i].innerText)
                    material_amount_duplicate = Number(mat_all[i].innerText)
                    $(material_amount_duplicate).val(material_amount)
//                    console.log("for mat duplicate",material_amount_duplicate)
                }
                for(var i=0;i<lab_all.length;i++)
                {
                    all_tot += Number(lab_all[i].innerText)
                    labour_amount_duplicate = Number(lab_all[i].innerText)
                    $(labour_amount_duplicate).val(labour_amount)
//                    console.log("for lab duplicate",labour_amount_duplicate)
                }
                for(var i=0;i<overhead_all.length;i++)
                {
                    all_tot += Number(overhead_all[i].innerText)
                    overhead_amount_duplicate = Number(overhead_all[i].innerText)
                    $(overhead_amount_duplicate).val(overhead_amount)
//                    console.log("for lab duplicate",overhead_amount_duplicate)
                }
//                console.log("ALL TOTAL SETTING :::::::: ",all_tot)
                $(total).html(all_tot)
                $(total_amount_duplicate).val(all_tot)
//                console.log("total_amount_duplicate2 :::::::: ",total_amount_duplicate)
    //            console.log("Total::::",total.value)
            }
         });

         $('input[class=labour_your_price]').change(function(event)
         {
            if(event && event.currentTarget && event.currentTarget.attributes && event.currentTarget.attributes.my_id)
            {
                var id = event.currentTarget.attributes.my_id.value
                var qty2 = '#labour_quantity-'+id+' span'
                var price2 = 'input[name=labour_your_price-'+id+']'
                var mat_amt = '#labour_amount-'+id+' span'
                 var total = '#total_amount'
                 var total_amount_duplicate = '#total_amount_duplicate'
                 var material_amount_duplicate = 'material_amount_duplicate-'+id
                 var labour_amount_duplicate = 'labour_amount_duplicate-'+id
                 var overhead_amount_duplicate = 'overhead_amount_duplicate-'+id
//                 console.log('material_amount_duplicate',material_amount_duplicate)
//                 console.log('labour_amount_duplicate',labour_amount_duplicate)
//                 console.log('overhead_amount_duplicate',overhead_amount_duplicate)
//                console.log('*************',$(material_amount_duplicate))
//                console.log($(price))
//                console.log($(mat_amt))
//                console.log("qty:::",qty)

                a2 = $(qty2).text()
                b2 = $(price2)[0].value

                var aa2 = a2.replace(/[^0-9.-]+/g,"");
                var aValue2 = parseFloat(aa2)
//                console.log("aValue",aValue2)

                var bb2 = b2.replace(/[^0-9.-]+/g,"");
                var bValue2 = parseFloat(bb2)
//                console.log("bValue",bValue2)

                var labour_amount = aValue2 * bValue2
                var lab_amt1 = $('#labour_amount-'+id+' span').text(labour_amount)
                $('[name="' + labour_amount_duplicate + '"]').val(labour_amount)
//                console.log('lab_amt1',$(lab_amt1))
//                console.log('material_amount_duplicate',$(mat_amt1_duplicate))
//                console.log("material_input_amount amt==========",$('.material_input_amount').val())
                var mat_all = $('.material_amount')
                var lab_all = $('.labour_amount')
                var overhead_all = $('.overhead_amount')
                var all_tot = 0.00
//                console.log('22222222222222222',mat_all)
                for(var i=0;i<mat_all.length;i++)
                {
                    all_tot += Number(mat_all[i].innerText)
                    material_amount_duplicate = Number(mat_all[i].innerText)
                    $(material_amount_duplicate).val(material_amount)
//                    console.log("for mat duplicate",material_amount_duplicate)
                }
                for(var i=0;i<lab_all.length;i++)
                {
                    all_tot += Number(lab_all[i].innerText)
                    labour_amount_duplicate = Number(lab_all[i].innerText)
                    $(labour_amount_duplicate).val(labour_amount)
//                    console.log("for lab duplicate",labour_amount_duplicate)
                }
                for(var i=0;i<overhead_all.length;i++)
                {
                    all_tot += Number(overhead_all[i].innerText)
                    overhead_amount_duplicate = Number(overhead_all[i].innerText)
                    $(overhead_amount_duplicate).val(overhead_amount)
//                    console.log("for lab duplicate",overhead_amount_duplicate)
                }
//                console.log("ALL TOTAL SETTING :::::::: ",all_tot)
                $(total).html(all_tot)
                $(total_amount_duplicate).val(all_tot)
//                console.log("total_amount_duplicate2 :::::::: ",total_amount_duplicate)
    //            console.log("Total::::",total.value)
            }
         });

         $('input[class=overhead_your_price]').change(function(event)
         {
            if(event && event.currentTarget && event.currentTarget.attributes && event.currentTarget.attributes.my_id)
            {
                var id = event.currentTarget.attributes.my_id.value
                var qty3 = '#overhead_quantity-'+id+' span'
                var price3 = 'input[name=overhead_your_price-'+id+']'
                var overhead_amt = '#overhead_amount-'+id+' span'
                 var total = '#total_amount'
                 var total_amount_duplicate = '#total_amount_duplicate'
                 var material_amount_duplicate = 'material_amount_duplicate-'+id
                 var labour_amount_duplicate = 'labour_amount_duplicate-'+id
                 var overhead_amount_duplicate = 'overhead_amount_duplicate-'+id
//                 console.log('material_amount_duplicate',material_amount_duplicate)
//                 console.log('labour_amount_duplicate',labour_amount_duplicate)
//                 console.log('overhead_amount_duplicate',overhead_amount_duplicate)
//                console.log('*************',$(material_amount_duplicate))
//                console.log($(price))
//                console.log($(mat_amt))
//                console.log("qty:::",qty)

                a3 = $(qty3).text()
                b3 = $(price3)[0].value

                var aa3 = a3.replace(/[^0-9.-]+/g,"");
                var aValue3 = parseFloat(aa3)
//                console.log("aValue3",aValue3)

                var bb3 = b3.replace(/[^0-9.-]+/g,"");
                var bValue3 = parseFloat(bb3)
//                console.log("bValue",bValue3)

                var overhead_amount = aValue3*bValue3

//                var overhead_amount = Number($(qty3).text())*Number($(price3)[0].value)
                var overhead_amt1 = $('#overhead_amount-'+id+' span').text(overhead_amount)
                $('[name="' + overhead_amount_duplicate + '"]').val(overhead_amount)
//                console.log('overhead_amt1',$(overhead_amt1))
//                console.log('material_amount_duplicate',$(mat_amt1_duplicate))
//                console.log("material_input_amount amt==========",$('.material_input_amount').val())
                var mat_all = $('.material_amount')
                var lab_all = $('.labour_amount')
                var overhead_all = $('.overhead_amount')
                var all_tot = 0.00
//                console.log('22222222222222222',overhead_all)
                for(var i=0;i<mat_all.length;i++)
                {
                    all_tot += Number(mat_all[i].innerText)
                    material_amount_duplicate = Number(mat_all[i].innerText)
                    $(material_amount_duplicate).val(material_amount)
//                    console.log("for mat duplicate",material_amount_duplicate)
                }
                for(var i=0;i<lab_all.length;i++)
                {
                    all_tot += Number(lab_all[i].innerText)
                    labour_amount_duplicate = Number(lab_all[i].innerText)
                    $(labour_amount_duplicate).val(labour_amount)
//                    console.log("for lab duplicate",labour_amount_duplicate)
                }
                for(var i=0;i<overhead_all.length;i++)
                {
                    all_tot += Number(overhead_all[i].innerText)
                    overhead_amount_duplicate = Number(overhead_all[i].innerText)
                    $(overhead_amount_duplicate).val(overhead_amount)
//                    console.log("for lab duplicate",overhead_amount_duplicate)
                }
//                console.log("ALL TOTAL SETTING :::::::: ",all_tot)
                $(total).html(all_tot)
                $(total_amount_duplicate).val(all_tot)
//                console.log("total_amount_duplicate2 :::::::: ",total_amount_duplicate)
    //            console.log("Total::::",total.value)
            }
         });

    })
})
