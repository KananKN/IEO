
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

function sweetAlertDel(productId) {
    // ตรวจสอบว่า product นี้มีข้อมูลเชื่อมโยงหรือไม่
    $.post("/product/check_product_reference", { id: productId }, function (res) {
        let warningMessage = "คุณแน่ใจหรือไม่ว่าต้องการลบสินค้านี้?";

        if (res.has_reference) {
            warningMessage = `
                สินค้านี้มีข้อมูลที่เชื่อมโยงกับโปรแกรมอื่นๆ<br>
                หากคุณลบ รายการที่เชื่อมโยงทั้งหมดจะถูกลบไปด้วย และไม่สามารถกู้คืนได้!
            `;  
        }

        swal({
            title: "แจ้งเตือน!",
            content: {
                element: "div",
                attributes: {
                    innerHTML: warningMessage
                },
            },
            icon: "warning",
            buttons: {
                cancel: {
                    text: "ยกเลิก",
                    value: null,
                    visible: true,
                    className: "btn btn-secondary",
                    closeModal: true,
                },
                confirm: {
                    text: "ลบข้อมูล",
                    value: true,
                    visible: true,
                    className: "btn btn-danger",
                    closeModal: true,
                },
            },
            dangerMode: true,
        }).then((willDelete) => {
            if (willDelete) {
                $.post("/product/delete_productSale", { id: productId }, function () {
                    swal("ลบข้อมูลเรียบร้อยแล้ว!", {
                        icon: "success",
                    }).then(() => location.reload());
                }).fail(function (xhr) {
                    const error = xhr.responseJSON?.message || "ไม่สามารถลบได้";
                    swal("เกิดข้อผิดพลาด", error, "error");
                });
            }
        });
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