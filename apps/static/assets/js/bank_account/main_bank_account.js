
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
            post("/bank_account/deleteBank", { id: id });
        }
    });
}



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
        $('[name="name_bankAccount"]').val('');
        $('[name="account_no"]').val('');
       


    } else if (mode == 'edit') {
        // $('form').attr('action', '/customer/edit');
        $('.modal-title').html('Edit');
        $('.c_add').hide()
        $('.c_edit').show()

        $('[name="id"]').val(data.id);
        $('[name="name_bankAccount"]').val(data.name);
        $('[name="account_no"]').val(data.account_number);
       
        
    }

}

function func_save(mode, x) {

    console.log(mode)
    x.attr('disabled', true);

    let details = {
        'name': $('[name="name_bankAccount"]').val(),
        'account_no': $('[name="account_no"]').val(),
        
    }
    if (details['name'].trim() == '') {
        check_fail('กรุณากรอกชื่อ')
        return
    } 
    
    if (mode === 'add') {
        fetch("/bank_account/addBank", {
            method: "post",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name: $('[name="name_bankAccount"]').val(),
                account_no: $('[name="account_no"]').val(),
            }),
        })
        .then((response) => {
            if (!response.ok) {
                return response.json().then((data) => { throw data });
            }
            return response.json();
        })
        .then((data) => {
            console.log(data);
            x.attr('disabled', true);
            location.reload();
        })
        .catch((error) => {
            console.error("Error:", error);
            swal({
                icon: "error",
                title: error.message || "เกิดข้อผิดพลาด",
                showConfirmButton: true
            });
            x.attr('disabled', false);
        });
    }
    
         else if (mode == 'edit') {
        // alert(mode)
        fetch("/bank_account/updateBank", {
                method: "post",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    id: $('[name="id"]').val(),
                    name: $('[name="name_bankAccount"]').val(),
                    account_no: $('[name="account_no"]').val(),
                  
                }),
            })
            .then((response) => {
                if (!response.ok) {
                    return response.json().then((data) => { throw data });
                }
                return response.json();
            })
            .then((data) => {
                console.log(data);
                x.attr('disabled',true);
                // swal({
                //     icon: "success",
                //     title: "Successfully edit customer!",
                //     confirmButtonText: "OK", // ตัวเลือกที่ถูก deprecated
                //     showConfirmButton: true,
                //     // timer: 1500
                // });
                location.reload();
            })
            .catch((error) => {
                console.error("Error:", error);
                swal({
                    icon: "error",
                    title: error.message || "เกิดข้อผิดพลาด",
                    showConfirmButton: true
                });
                 x.attr('disabled', false);
            });

    }




}