
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

    // ตั้ง action สำหรับการบันทึกจริง
    $('#myForm').attr('action', '/product/updateProductSale').attr('method', 'POST');
    $('#myForm').submit();



}




function sweetAlertDelImage (id, event) {
    if (event) {
        event.preventDefault();  // ✅ ป้องกันการรีโหลด
    }
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
            post("/product/delete_img", { id: id });
        }
    });
}
