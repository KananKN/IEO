
// delete
function post(path, params, method = "post") {
    const form = document.createElement("form");
    form.method = method;
    form.action = path;
    for (const key in params) {
        if (params.hasOwnProperty(key)) {
            const hiddenField = document.createElement("input");
            hiddenField.type = "hidden";
            hiddenField.name = key;
            hiddenField.value = params[key];
            form.appendChild(hiddenField);
        }
    }
    document.body.appendChild(form);
    form.submit();
}




function func_modal(mode, data) {
    console.log(mode, data)
    $('#modal-dialog').modal('show');

    if (mode == 'add') {
        // $('form').attr('action', '/customer/add');
        $('.modal-title').html('เพิ่มชื่อสกุลเงิน');
        $('.c_add').show()
        $('.c_edit').hide()
        $('[name="name"]').val('');
        $('[name="code"]').val('');
       


    } else if (mode == 'edit') {
        // $('form').attr('action', '/customer/edit');
        $('.modal-title').html('แก้ไขชื่อสกุลเงิน');
        $('.c_add').hide()
        $('.c_edit').show()

        $('[name="id"]').val(data.id);
        $('[name="name"]').val(data.name);
        $('[name="code"]').val(data.code);
       
        
    }

}
function submitExpenseForm() {

    Swal.fire({
        title: 'ยืนยันการบันทึก',
        text: 'คุณต้องการบันทึกข้อมูลค่าใช้จ่ายนี้หรือไม่?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'บันทึก',
        cancelButtonText: 'ยกเลิก',
        allowOutsideClick: false
    }).then((result) => {
    
        if (!result.isConfirmed) return;
    
        // const form = $('#expenseForm');
        const form = document.getElementById('expenseForm');
    
        // 🔥 ล้าง comma ก่อนส่ง
        // removeCommaBeforeSubmit(form);
        removeCommaBeforeSubmit($('#expenseForm'));
        const formData = new FormData(form);

    
        // 🔄 loading
        Swal.fire({
            title: 'กำลังบันทึก...',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
    
        $.ajax({
            url: '/account/expense/save',
            type: 'POST',
            // data: form.serialize(),
            data: formData,

            processData: false, // 🔥 จำเป็น
            contentType: false, // 🔥 จำเป็น
    
            success(res) {
                Swal.close(); // ✅ ปิด loading
    
                Swal.fire({
                    icon: 'success',
                    title: 'บันทึกสำเร็จ',
                    text: res.message || 'ระบบได้บันทึกข้อมูลเรียบร้อยแล้ว',
                    confirmButtonText: 'ตกลง'
                }).then(() => {
                    window.location.href = '/account/expense_claims_list';
                });
            },
    
            error(err) {
                Swal.close(); // ✅ ปิด loading
    
                const msg =
                    err.responseJSON?.message ||
                    err.responseText ||
                    'ไม่สามารถบันทึกข้อมูลได้';
    
                Swal.fire({
                    icon: 'error',
                    title: 'เกิดข้อผิดพลาด',
                    text: msg,
                    confirmButtonText: 'ปิด'
                });
            }
        });
    });
    
}

// function submitExpenseForm() {

//     $.ajax({
//         url: '/account/expense/save',
//         type: 'POST',
//         data: $('#expenseForm').serialize(),
//         success(res) {
//             alert('บันทึกสำเร็จ');
//             window.location.href = '/account/expense_claims_list'; // หรือหน้าที่ต้องการ
//         },
//         error(err) {
//             console.error(err);
//             alert('เกิดข้อผิดพลาดในการบันทึก');
//         }
//     });
// }


$(document).ready(function () {

    toggleClaimSection($('#claim_type').val());


    $('#requester_user_id').on('change', function () {
        const userId = $(this).val();
        console.log('Selected user ID:', userId);
        // ถ้าไม่เลือก user
        if (!userId) {
            $('#username').val('');
            $('#phone').val('');
            $('#email').val('');
            return;
        }

        $.ajax({
            url: `/account/get_user/${userId}`,
            type: 'GET',
            dataType: 'json',
            success: function (res) {
                if (res.status !== 'success') {
                    swal({
                        icon: 'error',
                        title: 'ผิดพลาด',
                        text: res.message
                    });
                    return;
                }

                const data = res.data;
                console.log(data);


                $('#username').val(data.username || '');
                $('#phone').val(data.phone || '');
                $('#email').val(data.email || '');
                $('#name').val(data.full_name || '');
                $('#bank_account').val(data.bank_account || '');
                $('#bank_name').val(data.bank_name || '');

                // 🔹 ถ้าจะเอาไปใส่ใน modal ด้วย
                // $('#modal-name').val(data.full_name || '');
                // 🔥 ตารางใน modal
                $('#modal-full-name').text(data.full_name || '-');
                $('#modal-bank-account').text(data.bank_account || '-');
                $('#modal-bank-name').text(data.bank_name || '-');
            },
            error: function (xhr) {
                let msg = 'ไม่สามารถดึงข้อมูลผู้ใช้ได้';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    msg = xhr.responseJSON.message;
                }

                swal({
                    icon: 'error',
                    title: 'เกิดข้อผิดพลาด',
                    text: msg
                });
            }
        });
    });

    // $('#claim_type').on('change', function () {
    //     const value = $(this).val();

    //     // ซ่อนทั้งหมดก่อน
    //     $('#staffSection').addClass('d-none');
    //     $('#childrenSection').addClass('d-none');

    //     // แสดงตามที่เลือก
    //     if (value === 'staff') {
    //         $('#staffSection').removeClass('d-none');
    //     } else if (value === 'children') {
    //         $('#childrenSection').removeClass('d-none');
    //     }
    // });

    //initExpenseSelect($('.expense-name-select').first());

    // $('.expense-name-select').each(function () {
    //     initExpenseSelect($(this));
    // });

    $('input[name^="expense_date["]').each(function () {
        initExpenseDatepicker($(this));
    });

    $('input[name^="pay_date["]').each(function () {
        initExpenseDatepicker($(this));
    });

    if (children_item && children_item.member_id) {
        $('#memberSelect')
            .val(children_item.member_id)
            .trigger('change');   // 🔥 สำคัญ
    }

    // if (children_item.expense_items && children_item.expense_items.length > 0) {
    //     children_item.expense_items.forEach(item => {
    //         addExpenseItemWithData(item);
    //     });
    //     console.log("data")
    //     console.log(children_item.expense_items.length)
    if (children_item && children_item.expense_items) {
        children_item.expense_items.forEach(item => {
            addExpenseItemWithData(item);
        });

        calculateTotal();
    }else{
        addExpenseItem(); 

    }
    
    $(document).on('input', '.number-comma', function () {
        const cursor = this.selectionStart;
        const oldLength = this.value.length;
    
        this.value = formatNumberWithComma(this.value);
    
        const newLength = this.value.length;
        this.selectionEnd = cursor + (newLength - oldLength);
    });
    
    
    $('#product_id').select2({

        placeholder: 'เลือกสินค้า',
        allowClear: true,
        width: '100%',
    
        ajax: {
            url: '/account/api/products',
            dataType: 'json',
            delay: 250,
    
            processResults: function (data) {
    
                let grouped = {};
    
                data.forEach(function(item){
    
                    if(!grouped[item.category]){
                        grouped[item.category] = [];
                    }
    
                    grouped[item.category].push({
                        id: item.id,
                        text: item.name
                    });
    
                });
    
                let results = [];
    
                Object.keys(grouped).forEach(function(cat){
                    results.push({
                        text: cat,
                        children: grouped[cat]
                    });
                });
    
                return { results: results };
    
            }
        }
    
    });
    
});
function toggleClaimSection(value) {
    $('#staffSection').addClass('d-none');
    $('#childrenSection').addClass('d-none');

    if (value === 'staff') {
        $('#staffSection').removeClass('d-none');
    } else if (value === 'children') {
        $('#childrenSection').removeClass('d-none');
    }
}

$('#claim_type').on('change', function () {
    toggleClaimSection($(this).val());
});

/* ---------- STAFF ---------- */
let staffIndex = 0;
    
function addStaffRow(item ={}) {
  staffIndex++;
  const row = `
    <tr>
      <td class="text-center">${staffIndex}</td>
      <td>
       <select class="form-control expense-name-select" name="receiver_staff[]">
           <option value="">-- เลือกผู้รับเงิน --</option>
       </select>
     </td>
      <td>
        <input type="hidden" class="form-control" value="${item.id}" name="expense_staff_items_id[]">
        <input type="text" class="form-control" value="${item.item_name || ''}" name="item_name[]">
      </td>
      <td>
        <input type="text" class="form-control text-end staff-amount number-comma"
               name="staff_amount[]" step="0.01" 
               value="${item.amount ?? ''}"
                oninput="handleNumberInput(this); calcStaffTotal();"
                onblur="formatToTwoDecimal(this)">
      </td>
      <td class="text-center">
        <button class="btn btn-sm btn-danger" onclick="removeRow(this, calcStaffTotal)">✕</button>
      </td>
    </tr>
  `;
  document.getElementById('staffTableBody').insertAdjacentHTML('beforeend', row);

  const $newSelect = $('#staffTableBody').find('.expense-name-select').last();
  initExpenseSelect($newSelect);
  
    // ⭐ set ค่า select ตอน edit
  if (item.receiver_type && item.receiver_id) {

    let value = item.receiver_type + ':' + item.receiver_id;

    let option = new Option(item.receiver_name, value, true, true);

    $newSelect.append(option).trigger('change');
}


}

function formatAllNumberComma() {
    $('.number-comma').each(function () {
        // this.value = formatNumberWithComma(this.value);
        formatToTwoDecimal(this);

    });
}



// ใส่คอมม่า
function formatNumber(val) {
    if (val === '' || val === null) return '';
    val = val.toString().replace(/,/g, '');
    if (isNaN(val)) return '';
    return Number(val).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}
// เอาคอมม่าออก (ไว้คำนวณ / ส่ง backend)

function unformatNumber(val) {
    if (!val) return 0;
    return parseFloat(val.toString().replace(/,/g, '')) || 0;
}

function handleNumberInput(el) {
    let value = el.value;

    // เอา comma ออก
    value = value.replace(/,/g, '');

    // อนุญาตเฉพาะเลขกับ .
    value = value.replace(/[^0-9.]/g, '');

    // กันหลายจุด
    const parts = value.split('.');
    if (parts.length > 2) {
        value = parts[0] + '.' + parts.slice(1).join('');
    }

    // จำกัดทศนิยม 2 ตำแหน่ง
    const [intPart, decPart] = value.split('.');
    if (decPart !== undefined) {
        value = intPart + '.' + decPart.slice(0, 2);
    }

    el.value = value;
}


function formatToTwoDecimal(el) {
    let val = el.value.replace(/,/g, '');

    if (val === '' || val === '.') {
        el.value = '0.00';
        return;
    }

    const num = parseFloat(val);
    if (isNaN(num)) {
        el.value = '0.00';
        return;
    }

    el.value = num.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}


function calcStaffTotal() {
  let total = 0;
  //document.querySelectorAll('.staff-amount').forEach(el => {
  //  total += parseFloat(el.value) || 0;
  //});
  //document.getElementById('staffTotal').innerText = total.toFixed(2);
    $('.staff-amount').each(function () {
        const val = unformatNumber($(this).val());
        total += val;
    });

    // แสดงผล (มี comma)
    $('#staffTotal').text(formatNumber(total));
    $('#staff_total_amount').val(total.toFixed(2)); // เก็บไว้ส่ง backend
}

/* ---------- shared ---------- */
function removeRow(btn, callback) {
    btn.closest('tr').remove();
    if (callback) callback();
}

//---- end staff ----//

$('#memberSelect').on('change', function () {
    const memberId = $(this).val();
    const $project = $('#projectSelect');

    $project.empty();

    if (!memberId) {
        $project
            .append('<option value="">กรุณาเลือกเด็กก่อน</option>')
            .prop('disabled', true);
        return;
    }

    $.getJSON(`/account/get_member_orders/${memberId}`, function (res) {

        if (res.data.length === 0) {
            $project
                .append('<option value="">ไม่มีโครงการ</option>')
                .prop('disabled', true);
            return;
        }

        $project.append('<option value="">เลือกโครงการ</option>');

        res.data.forEach(o => {
            $project.append(
                `<option value="${o.project_id}">${o.project_name}</option>`
            );
        });

        $project.prop('disabled', false);
        // ✅ auto select project ตอน edit
        if (children_item && children_item.project_id) {
            $project.val(children_item.project_id);
        }

    })
    .fail(function () {
        alert('โหลดโครงการไม่สำเร็จ');
    });
});

//------ ดึงข้อมูลรายเชื่อผู้รับเงิน มาใส่ใน select -------//
/*
$(function () {
    $.getJSON('/account/expense/receivers', function (data) {
        $('select[name="expense_name[]"]').each(function () {
            let $select = $(this);
            $select.empty();
            //<option value="">-- เลือกผู้รับเงิน --</option>
            $select.append('<option value="">-- เลือกผู้รับเงิน --</option>');
    
            
            data.forEach(item => {
                $select.append(`
                    <option value="${item.type}:${item.id}">
                        ${item.name}
                    </option>
                `);
            });
        });
    });
});

*/


//----- หมวดค่าใช้จ่าย -----//
let treeData = [];
    $(function () {
        if (EXIST_STAFF_ITEMS.length > 0) {
            EXIST_STAFF_ITEMS.forEach(item => {
                // console.log('Adding existing staff item:', item);
                addStaffRow(item);
            });
        } else {
            // เปิดมาครั้งแรก → มี 1 แถว
            addStaffRow();
        }
        formatAllNumberComma();
        calcStaffTotal();

        $('#expenseTree').jstree({
            core: {
                data: {
                    url: "/account/expense_categories/tree",
                    dataType: "json"
                },
                check_callback: true
            },
            types: {
                category: { icon: "fa fa-folder" },
                item: { icon: "fa fa-file" }
            },
            plugins: ["types", "search"]
        });

        
    });
    
    

    
    $('#expenseTree').on("select_node.jstree", function (e, data) {
        const node = data.node;
    
        if (node.type === 'item') {

            const path = data.instance.get_path(node, ' > ');
            console.log(node);
    
            $('#expense_subcategory_id').val(node.id.replace('item-', ''));
            $('#expense_category_id').val(node.original.category_id);
            $('#expense_claims').val(node.text);
            $('#expenseModal').modal('hide');
        }
    });

    let to = false;
    $('#treeSearch').keyup(function () {
        if (to) clearTimeout(to);
        to = setTimeout(function () {
            $('#expenseTree').jstree(true).search($('#treeSearch').val());
        }, 250);
    });
    
    function renderTree(data, container, path = []) {
        container.empty();
    
        data.forEach(item => {
            const li = $('<li>');
    
            const title = $('<span>')
                .text(item.text)
                .addClass(item.children.length ? 'fw-bold' : 'expense-leaf')
                .click(() => {
                    if (!item.children.length) {
                        selectCategory(item, path);
                    }
                });
    
            li.append(title);
    
            if (item.children && item.children.length) {
                const ul = $('<ul>').addClass('ms-3');
                renderTree(item.children, ul, [...path, item.text]);
                li.append(ul);
            }
    
            container.append(li);
        });
    }

    $('#expenseTree').on('loaded.jstree', function () {

        // 1. อ่านค่า subcategory ที่มีอยู่แล้ว
        const subId = $('#expense_subcategory_id').val();
        console.log('EDIT MODE subId =', subId);

        // 2. ถ้ามีค่า → สั่ง jsTree เลือก
        if (subId) {
            const nodeId = 'item-' + subId;

            $('#expenseTree').jstree('select_node', nodeId);
            $('#expenseTree').jstree('open_node', nodeId);
        }
    });

    $('#expenseTree').on("select_node.jstree", function (e, data) {
        const node = data.node;
    
        if (node.type === 'item') {
            $('#expense_claims').val(node.text);
            $('#expense_subcategory_id').val(node.id.replace('item-', ''));
            $('#expense_category_id').val(node.original.category_id);
        }
    });
    
    
    
    function selectCategory(item, path) {
        $('#expense_category_id').val(item.id);
        $('#expense_subcategory_id').val(item.category_id);
        $('#expense_claims').val([...path, item.name].join(' > '));
        $('#expenseModal').modal('hide');
    }


    
    function initExpenseSelect($el) {

        if ($el.hasClass('select2-hidden-accessible')) {
            $el.select2('destroy');
        }
    
        $el.select2({
            placeholder: '-- เลือกผู้รับเงิน --',
            allowClear: true,
            width: '100%',
    
            ajax: {
                url: '/account/expense/receivers',
                dataType: 'json',
                delay: 250,
                processResults: function (data) {
    
                    let groups = {};
    
                    data.forEach(function(item){
    
                        if(!groups[item.type]){
                            groups[item.type] = [];
                        }
    
                        groups[item.type].push({
                            id: item.type + ':' + item.id,
                            text: item.name
                        });
    
                    });
    
                    let results = [];
    
                    Object.keys(groups).forEach(function(type){
    
                        results.push({
                            text: type.charAt(0).toUpperCase() + type.slice(1),
                            children: groups[type]
                        });
    
                    });
    
                    return { results: results };
                }
            }
        });
    
    }
        
    


    

function calculateTotal() {
    let total = 0;
    
    // $('.amount').each(function () {
    //     const val = parseFloat($(this).val());
    //     if (!isNaN(val)) {
    //         total += val;
    //     }
    // });
    $('.amount').each(function () {
        const val = unformatNumber($(this).val());
        total += val;
    });

    

    // $('#totalAmount').text(total.toFixed(2));
    $('#totalAmount').text(formatNumber(total));

    $('#children_total_amount').val(total.toFixed(2)); // เก็บไว้ส่ง backend

    let total_ref = 0 
    
    $('.amount_before_exchange').each(function () {
        const val_ref = parseFloat($(this).val());
        if (!isNaN(val_ref)) {
            total_ref += val_ref;
        }
    });

    $('#ref_total').text(total_ref.toFixed(2));
    // $('#ref_total').text(formatNumber(total));

    $('#ref_total_amount').val(total_ref.toFixed(2)); // เก็บไว้ส่ง backend


}
    


/* ---------- COMMON ---------- */
function removeRow(btn, callback) {
    btn.closest('tr').remove();
    //calculateStaffTotal();
    // รี index
    staffIndex = 0;
    $('#staffTableBody tr').each(function () {
        staffIndex++;
        $(this).find('td:first').text(staffIndex);
    });

    if (callback) callback();
}

function removeExpenseItem(btn) {
    btn.closest('.expense-item').remove();
    calculateTotal();
}

function reindexExpenseItems() {
    $('.expense-item').each(function (i) {
        $(this).find('.expense-index').text(i + 1);
    });
}

$(document).on('click', '.btn-remove-expense', function () {
    $(this).closest('.expense-item').remove();
    reindexExpenseItems();
});


function initExpenseDatepicker($el) {
    $el.datepicker({
        format: 'dd/mm/yyyy',
        autoclose: true,
        todayHighlight: true
    });
    

}

function validateForm() {

    let requester_user = $('#requester_user_id').val();
    let claimType = $('#claim_type').val();
    let creationDate = $('input[name="creation_date"]').val();
    let subcategory = $('input[name="expense_subcategory_id"]').val();
    let expense_date = $('input[name="expense_date"]').val();
    // let totalAmount = parseFloat($('#total_amount').val() || 0);
    let product_id = $('#product_id').val();
     // 2) ตรวจวันที่
     if (!creationDate) {
        check_fail_claim('กรุณาเลือกวันที่');
        return;
    }
    
    if (!product_id) {
        Swal.fire({
            icon: 'warning',
            title: 'ข้อมูลไม่ครบ',
            text: 'กรุณาเลือกสินค้า'
        });
        return;
    }
   
    // 3) เลือก staff
    // if (!requester_user) {
    //     check_fail_claim('กรุณาเลือกผู้ขอเบิก');
    //     return;
    // }
    // 1) ตรวจประเภท
    // if (!claimType) {
    //     alert('กรุณาเลือกผู้รับการเบิก');
    //     return;
    // }

    // 3) ตรวจจำนวนรายการ
    let itemCount = 0;

    if (claimType === 'staff') {
        itemCount = $('.staff-item').length;
        if (!subcategory) {
            check_fail_claim('กรุณาเลือกประเภทการเบิก');
            return;
        }

        if (!expense_date) {
            check_fail_claim('กรุณากรอกวันที่จ่าย');
            return;
        }

        let hasAmount = false;
        let hasInvalid = false;
        let hasInvalidReceiver = false;

        // ===== check amount =====
        $('input[name="item_name[]"]').each(function () {
            if (!this.value) {
                hasInvalid = true;
                $(this).addClass('is-invalid'); // 🔥 highlight ช่องผิด
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        $('input[name="staff_amount[]"]').each(function () {
            const val = parseFloat($(this).val());
            if (!isNaN(val) && val > 0) {
                hasAmount = true;
            }
        });
        $('select[name="receiver_staff[]"]').each(function () {
            if (!this.value) {
                hasInvalidReceiver = true;
                $(this).addClass('is-invalid'); // 🔥 highlight ช่องผิด
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        if (hasInvalid) {
            Swal.fire({
                icon: 'warning',
                title: 'ข้อมูลไม่ครบ',
                text: 'กรุณากรอกรายการให้ครบทุกรายการ'
            });
            return;
        }
        if (hasInvalidReceiver) {
            Swal.fire({
                icon: 'warning',
                title: 'ข้อมูลไม่ครบ',
                text: 'กรุณาเลือก Supplier ให้ครบทุกแถว'
            });
            return;
        }

        if (!hasAmount) {
            Swal.fire({
                icon: 'warning',
                title: 'ข้อมูลไม่ครบ',
                text: 'กรุณากรอกจำนวนเงิน'
            });
            return;
        }

    } else if (claimType === 'children') {

        itemCount = $('.children-item').length;
        if (!$('select[name="member_id"]').val()) {
            Swal.fire({
                icon: 'warning',
                title: 'ข้อมูลไม่ครบ',
                text: 'กรุณาเลือกสมาชิก (Member)'
            });
            return;
        }

        
        

        if (!$('select[name="project_id"]').val()) {
            Swal.fire({
                icon: 'warning',
                title: 'ข้อมูลไม่ครบ',
                text: 'กรุณาเลือกโครงการ (Project)'
            });
            return;
        }
    
        let hasAmount = false;
        let hasInvalidReceiver = false;

        // ===== check amount =====
        $('input[name="amount[]"]').each(function () {
            const val = parseFloat($(this).val());
            if (!isNaN(val) && val > 0) {
                hasAmount = true;
            }
        });

        // ===== check receiver =====
        $('select[name="receiver[]"]').each(function () {
            if (!this.value) {
                hasInvalidReceiver = true;
                $(this).addClass('is-invalid'); // 🔥 highlight ช่องผิด
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        if (hasInvalidReceiver) {
            Swal.fire({
                icon: 'warning',
                title: 'ข้อมูลไม่ครบ',
                text: 'กรุณาเลือก Supplier ให้ครบทุกแถว'
            });
            return;
        }

        if (!hasAmount) {
            Swal.fire({
                icon: 'warning',
                title: 'ข้อมูลไม่ครบ',
                text: 'กรุณากรอกจำนวนเงินอย่างน้อย 1 รายการ'
            });
            return;
        }
    }

    // if (itemCount === 0) {
    //     alert('กรุณาเพิ่มอย่างน้อย 1 รายการ');
    //     return;
    // }

    // 4) ตรวจยอดรวม
    // if (totalAmount <= 0) {
    //     alert('ยอดรวมต้องมากกว่า 0');
    //     return;
    // }

    // 5) ผ่าน → submit
    submitExpenseForm();
}


function formatNumberWithComma(value) {
    if (!value) return '';
    value = value.toString().replace(/,/g, '');
    const parts = value.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
}

function formatCommaSmart(el) {
    if ($(el).is('input, textarea')) {
        el.value = formatNumberWithComma(el.value);
    } else {
        const raw = $(el).text().replace(/,/g, '');
        $(el).text(formatNumberWithComma(raw));
    }
}



function removeCommaBeforeSubmit(form) {
    $(form).find('.number-comma').each(function () {
        this.value = this.value.replace(/,/g, '');
    });
}


function check_fail_claim(msg){
    Swal.fire({
        icon: 'warning',
        title: 'ข้อมูลไม่ครบ',
        text: msg
    });
    return;
    
}

$('.btn-view-bank').on('click', function () {
    const itemId = $(this).data('item-id');

    // reset ก่อน (กันข้อมูลค้าง)
    $('#name').val('');
    $('#bank_name').val('');
    $('#bank_account').val('');

    $.get(
        `/account/expense/children-item/${itemId}/receiver`,
        function (res) {
            $('#name').val(res.name || '-');
            $('#bank_name').val(res.bank_name || '-');
            $('#bank_account').val(res.bank_account || '-');
        }
    );
});

function sweetAlertDelfile(id_file,type_staff,claim_id) {
    swal({
        title: "Are you sure?",
        text: "Delete?",
        icon: "error",
        buttons: {
            cancel: {
                text: "Cancel",
                value: null,
                visible: true,
                className: "btn btn-dark",
                closeModal: true,
            },
            confirm: {
                text: "Yes, Delete.",
                value: true,
                visible: true,
                className: "btn btn-danger",
                closeModal: true,
            },
        },
    }).then((result) => {
        if (result.dismiss !== "cancel") {
            post("/account/delete_file", {
                id_file: id_file,
                type_staff: type_staff,
                claim_id: claim_id,
            });
        }
    });
}


function validateFile(input) {
    const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png']; // นามสกุลไฟล์ที่อนุญาต
    const file = input.files[0];

    if (file) {
        const fileExtension = file.name.split('.').pop().toLowerCase(); // ดึงนามสกุลไฟล์

        if (!allowedExtensions.includes(fileExtension)) {
            check_fail('อนุญาตให้เลือกเฉพาะไฟล์ PDF, JPG, JPEG, PNG เท่านั้น!');
            input.value = ''; // เคลียร์ค่า input
        }
    }
}