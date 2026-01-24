
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

function sweetAlertDel(id, x) {

    swal({
        title: "ยืนยันการลบ?",
        text: "ข้อมูลนี้จะไม่สามารถกู้คืนได้",
        icon: "warning",
        buttons: {
            cancel: {
                text: "ยกเลิก",
                visible: true,
                className: "btn btn-secondary"
            },
            confirm: {
                text: "ลบ",
                className: "btn btn-danger"
            }
        },
        dangerMode: true,
    }).then((willDelete) => {

        if (!willDelete) return;

        x.prop('disabled', true);

        fetch(`/account/delete_claim/${id}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                swal("สำเร็จ", data.message, "success")
                    .then(() => location.reload());
            } else {
                throw new Error(data.message);
            }
        })
        .catch(error => {
            swal("ลบข้อมูลไม่สำเร็จ", error.message, "error");
            x.prop('disabled', false);
        });
    });
}





function setEditValue(data){
    // console.log(data)
    $("#id-update").val(data.id);
    $("#name-update").val(data.name);
    // $("#description-update").val(data.description);
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

function func_save(mode, x) {

    console.log(mode)
    x.attr('disabled', true);

    let details = {
        'name': $('[name="name"]').val(),
        'code': $('[name="code"]').val(),
        
    }
    if (details['name'].trim() == '') {
        check_fail('กรุณากรอกชื่อสกุลเงิน');
        x.attr('disabled', false);
        return
    } 
    if (details['code'].trim() == '') {
        check_fail('กรุณากรอกตัวอักษรสกุลเงิน');
        x.attr('disabled', false);
        return
    } 
    
        if (mode == 'add') {
            fetch("/account/add_currencies", {
                    method: "post",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({

                        name: $('[name="name"]').val(),
                        code: $('[name="code"]').val(),
                    
                    }),
                })
                .then(async (response) => {
                    const data = await response.json();
                
                    if (!response.ok) {
                        // ❗ error จาก backend
                        throw data;
                    }
                
                    return data;
                })
                .then((data) => {
                    console.log(data);
                    x.attr('disabled',true);
                    // swal({
                    //     icon: "success",
                    //     title: "Successfully added customer!",
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
                        title: "Error",
                        text: error.message || "เกิดข้อผิดพลาด",
                        confirmButtonText: "OK",  // ✅ ใช้ได้กับ Swal.fire()
                        showConfirmButton: true
                    });
                    x.attr('disabled', false);
                });


        } else if (mode == 'edit') {
        // alert(mode)
        fetch("/account/edit_currencies", {
                method: "post",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    id: $('[name="id"]').val(),
                    name: $('[name="name"]').val(),
                    code: $('[name="code"]').val(),
                  
                }),
            })
            .then(async (response) => {
                const data = await response.json();
            
                if (!response.ok) {
                    // ❗ error จาก backend
                    throw data;
                }
            
                return data;
            })
            .then((data) => {
                console.log(data);
                x.attr('disabled',true);
                location.reload();
            })
            .catch((error) => {
                console.error("Error:", error);
                swal({
                    icon: "error",
                    title: "Error",
                    text: error.message || "เกิดข้อผิดพลาด",
                    confirmButtonText: "OK", // ตัวเลือกที่ถูก deprecated
                    showConfirmButton: true,
                });
                 x.attr('disabled', false);
            });

    }




}