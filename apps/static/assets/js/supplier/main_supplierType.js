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

function func_save(mode, x) {
    console.log("Saving...");

    let name = $('[name="name_supplier"]').val();
    let description = $('[name="n_description"]').val();

    if (name == '') {
       return check_fail('กรุณากรอกชื่อ')
    }

    if (mode == 'add') {
            fetch("/supplier/addSupplier", {
                        method: "post",
                        headers: {
                        "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                        name, 
                        description
                        
                        }),
                  })
                  .then((response) => response.json())
                  .then((data) => {
                        console.log(data);
                        x.attr('disabled',true);
                        if (data.status === "Error") {
                            swal({
                                icon: "error",
                                title: "เกิดข้อผิดพลาด!",
                                text: data.message,
                                confirmButtonText: "ตกลง",
                            });
                             x.attr('disabled',false);
                        } else {
                            swal({
                                icon: "success",
                                title: "บันทึกสำเร็จ!",
                                text: data.message,
                                confirmButtonText: "ตกลง",
                            }).then(() => {
                                location.reload();
                            });
                        }
                  })
                  .catch((error) => {
                        console.error("Error:", error);
                        swal({
                        icon: "error",
                        title: "Error adding Supplier Type!",
                        confirmButtonText: "OK",  // ✅ ใช้ได้กับ Swal.fire()
                        showConfirmButton: true
                        });
                        x.attr('disabled', false);
                  });


      }else if (mode == 'edit'){

        let id = $('[name="id-update"]').val();                
            fetch("/supplier/editSupplier", {
                        method: "post",
                        headers: {
                        "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                              id,
                              name, 
                              description

                        }),
                  })
                  .then((response) => response.json())
                  .then((data) => {
                        console.log(data);
                        x.attr('disabled', true);  // ปิดการใช้งานปุ่มหลังการบันทึก
                        
                        if (data.status === "Error") {
                            swal({
                                icon: "error",
                                title: "เกิดข้อผิดพลาด!",
                                text: data.message,
                                confirmButtonText: "ตกลง",
                            });
                            x.attr('disabled', false);

                        } else {
                            swal({
                                icon: "success",
                                title: "บันทึกสำเร็จ!",
                                text: data.message,
                                confirmButtonText: "ตกลง",
                            }).then(() => {
                                location.reload();
                            });
                        }
                  })
                  .catch((error) => {
                        console.error("Error:", error);
                        swal({
                        icon: "error",
                        title: "Error adding Fees!",
                        confirmButtonText: "OK",  // ✅ ใช้ได้กับ Swal.fire()
                        showConfirmButton: true
                        });
                        x.attr('disabled', false);
                  });
      }
      
    
    // ตั้ง action สำหรับการบันทึกจริง
    

}

function func_modal(mode, data) {
    console.log(mode, data)
    $('#modal-dialog').modal('show');

    if (mode == 'add') {
        $('form').attr('action', '/supplier/addFees');
        $('.modal-title').html('Add');
        $('.c_add').show()
        $('.c_edit').hide()
        $('.modal-title').html('Add');
        $('[name="name_supplier"]').val('');
        $('[name="n_description"]').val('');
       


    } else if (mode == 'edit') {
        // $('form').attr('action', '/customer/edit');
        $('.modal-title').html('Edit');
        $('.c_add').hide()
        $('.c_edit').show()

        $('[name="id-update"]').val(data.data_sup.id);
        $('[name="name_supplier"]').val(data.name);
        $('[name="n_description"]').val(data.description);
       
        
    }

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
            post("/supplier/deleteSupplier", { id: id });
        }
    });
}