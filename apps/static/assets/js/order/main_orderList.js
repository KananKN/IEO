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

       fetch("/lead/check_statusLead", {
            method: "post",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({

                id: $('[name="id"]').val(),
                status: $('[name="status_mode"]').val(),
                remask: $('[name="remask"]').val(),
            
            }),
        })
        .then((response) => response.json())
        .then((data) => {
            console.log(data);
            x.attr('disabled',true);
            swal({
                icon: "success",
                title: "Successfully!",
                timer: 1500
            });

            location.reload();
        })
        .catch((error) => {
            console.error("Error:", error);
            swal({
                icon: "error",
                title: "Error !",
                confirmButtonText: "OK",  // ✅ ใช้ได้กับ Swal.fire()
                showConfirmButton: true
            });
            x.attr('disabled', false);
        });     
    
    
}