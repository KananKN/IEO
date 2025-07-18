$("#w_start").datepicker({
    todayHighlight: true,
    format: "dd-mm-yyyy",
}).on("changeDate", function(e) {
    // ดึงวันที่ที่ถูกเลือกจาก #w_start
    var startDate = e.date;
    
    // let initialSelected = $("#i_period").find("option:selected").data("period");
    // console.log("term_perid :",initialSelected)
    // คำนวณวันที่ +1 ปี
//     var endDate = new Date(startDate);
//     endDate.setFullYear(endDate.getFullYear() + 1);
//     endDate.setDate(endDate.getDate() - 1);

//     // อัปเดตค่าเริ่มต้นของ #w_end
//     $("#w_end").datepicker("setDate", endDate);
});
$("#w_end").datepicker({
    todayHighlight: true,
    format: "dd-mm-yyyy",
});
// de
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

function sweetAlertDel(id) {
    swal({
        title: "Are you sure?",
        text: "Delete!",
        icon: "error",
        buttons: {
            cancel: {
                text: "Cancel",
                value: null,
                visible: true,
                className: "btn btn-default",
                closeModal: true,
            },
            confirm: {
                text: "Delete",
                value: true,
                visible: true,
                className: "btn btn-danger",
                closeModal: true,
            },
        },
    }).then((result) => {
        if (result.dismiss !== "cancel") {
            post("product/deletePeriod", { id: id });
        }
    });
}
function sweetAlertDel_all(id) {
    swal({
        title: "Are you sure?",
        text: "Delete!",
        icon: "warning",
        buttons: {
            cancel: {
                text: "Cancel",
                value: null,
                visible: true,
                className: "btn btn-default",
                closeModal: true,
            },
            confirm: {
                text: "Delete",
                value: true,
                visible: true,
                className: "btn btn-danger",
                closeModal: true,
            },
        },
    }).then((result) => {
        if (result.dismiss !== "cancel") {
            post("/device/delete_all", { id: id });
        }
    });
}
// const getForUpdate = (id, email) => {
//     $("#id-update").val(id);
//     $("#email-update").val(email);
// };


function setEditValue(data){
    // console.log(data)
    $("#id-update").val(data.id);
    $("#name-update").val(data.name);
    $("#description-update").val(data.description);
}


function func_modal(mode, data) {
    console.log(mode, data)
    $('#modal-dialog').modal('show');

    if (mode == 'add') {
        // $('form').attr('action', '/customer/add');
        $('.modal-title').html('Add');
        $('.c_add').show()
        $('.c_edit').hide()
        $('.modal-title').html('Add');
        $('[name="name"]').val('');
       


    } else if (mode == 'edit') {
        // $('form').attr('action', '/customer/edit');
        $('.modal-title').html('Edit');
        $('.c_add').hide()
        $('.c_edit').show()

        $('[name="id"]').val(data.id);
        $('[name="name"]').val(data.name);
       
        
    }

}

function func_save(mode, x) {
    console.log("Saving...");

    let values = [];
    let duplicates = false;

    $('input[name="term_year[]"]').each(function () {
        let val = $(this).val();
        if (val) {
            if (values.includes(val)) {
                duplicates = true;
                return false; // พบปีซ้ำ
            }
            values.push(val);
        }
    });

    if (duplicates) {
        alert('ไม่สามารถบันทึกได้ เพราะปีซ้ำกัน');
        return; // ⛔ หยุดฟังก์ชัน ไม่ submit ฟอร์ม
    }

    // ✅ อัปเดตค่า checkbox ให้เป็น '0' หรือ '1'
    $('.vat-checkbox').each(function () {
        this.value = this.checked ? '1' : '0';
        this.checked = true; // ✅ บังคับให้ checkbox ถูกส่งเสมอ
    });

    // ✅ ถ้าไม่มีปีซ้ำ ให้ตั้งค่า action และส่งฟอร์ม
    $('#myForm')
        .attr('action', '/product/addProductSale')
        .attr('method', 'POST')
        .submit();

   



}