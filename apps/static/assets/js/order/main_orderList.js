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
                post("/order/delete_order_list", {
                    id: id
                });
            }
        });
    }

function func_save(x){
    
    x.attr('disabled', true);   

    const data = {
        product_id: $('[name="name_project"]').val(),
        first_name: $('[name="fullname"]').val(),
        last_name: $('[name="lastname"]').val(),
        first_nameEN: $('[name="first_nameEN"]').val(),
        last_nameEN: $('[name="lastnameEN"]').val(),
        nickname: $('[name="nickname"]').val(),
        year: $('[name="year"]').val(),
        email: $('[name="email"]').val(),
        tel: $('[name="phone"]').val(),
        agency_id: $('[name="agency"]').val(),
        category_id: $('[name="category"]').val(),
        country_id: $('[name="country"]').val(),
        gender: $('input[name="gender"]:checked').val(),
        line_id: $('[name="line_id"]').val(),
        address: $('[name="address"]').val(),
    };

    // ✅ ตรวจสอบฟิลด์ที่ต้องไม่ว่าง
    const required_fields = ["product_id", "first_name", "last_name", "first_nameEN", "last_nameEN", "email", "tel", "category_id", "country_id", "gender", "address", "line_id"];
    let missing_fields = [];

    required_fields.forEach(field => {
        if (!data[field] || String(data[field]).trim() === '') {
            missing_fields.push(field);
        }
    });

    if (missing_fields.length > 0) {
        swal({
            icon: "warning",
            title: "กรุณากรอกข้อมูลให้ครบถ้วน",
            //text: `ขาด: ${missing_fields.join(", ")}`,
        });
        x.attr('disabled', false);
        return; // ❌ ไม่ส่ง request ถ้าข้อมูลไม่ครบ
    }

       fetch("/order/create_order", {
            method: "post",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({

                product_id: $('[name="name_project"]').val(),
                first_name: $('[name="fullname"]').val(),
                last_name: $('[name="lastname"]').val(),
                first_nameEN: $('[name="first_nameEN"]').val(),
                last_nameEN: $('[name="lastnameEN"]').val(),
                nickname:$('[name="nickname"]').val(),
                year:$('[name="year"]').val(),
                email:$('[name="email"]').val(),
                tel:$('[name="phone"]').val(),
                agency_id:$('[name="agency"]').val(),
                category_id:$('[name="category"]').val(),
                country_id:$('[name="country"]').val(),
                gender:$('input[name="gender"]:checked').val(),
                line_id:$('[name="line_id"]').val(),
                address:$('[name="address"]').val(),
            
            
            }),
        })
        .then((response) => response.json())
        .then((data) => {
            console.log(data);
            if (data.status === "error") {
                    swal({
                        icon: "error",
                        text: data.message,
                        // text: data.message,
                        confirmButtonText: "ตกลง",
                    });
                    x.attr('disabled', false);

                } else {
                    swal({
                        icon: "success",
                        title: "บันทึกสำเร็จ!",
                        // text: data.message,
                        confirmButtonText: "ตกลง",
                    }).then(() => {
                        //location.reload();
                        window.location.href = "/order";
                    });
                }
        })
        .catch((error) => {
            console.error("Error:", error);
            swal({
                icon: "error",
                //   title: "uername มีคนใช้แล้ว กรุณาเปลี่ยน",
                text: data.message,
                confirmButtonText: "OK",  // ✅ ใช้ได้กับ Swal.fire()
                showConfirmButton: true
            });
            //      .attr('disabled', false);
        });
    
    
}