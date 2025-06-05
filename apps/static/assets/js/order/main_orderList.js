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

$(document).ready(function() {
    loadDataTable();
});


function loadDataTable() {
    if ($.fn.DataTable.isDataTable('#data-table-responsive')) {
        $('#data-table-responsive').DataTable().destroy(); // ลบ DataTable เดิมก่อน
    }

    const table = $('#data-table-responsive').DataTable({
        responsive: true,
        processing: true,
        serverSide: true,
        ajax: {
            url: "/order/get_order1",
            type: "POST",
            data: function(d) { 
                return JSON.stringify(d); 
            },
            contentType: "application/json",
            dataType: "json"
        },
        columns: [
            { data: "id", className: "text-center" },
            { data: null,
                render: function(data, type, row) {
                    const rowData = JSON.stringify(row).replace(/"/g, '&quot;'); 
                    return `
                    <a href="/order/order_update/${data.data_user.id}"  >
                    ${data.order_number}</a>
                    </a> `;
                }
            
            } ,
            { data: "customer_name"} ,
            { data: "product_name" },
            { data: "price",
                render: function(data, type, row) {
                    if (type === 'display' || type === 'filter') {
                        // Format ตัวเลขให้มีเครื่องหมายคอมม่าและ 2 ทศนิยม
                        return Number(data).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                    }
                    return data; // ถ้าไม่ใช่สำหรับการแสดงผล ให้ส่งคืนค่าตามเดิม
                } 
            },
            
            {
                data: "created_at",
                render: function (data) {
                    const d = new Date(data);
                    return d.toLocaleDateString("th-TH"); // แสดงวันที่แบบไทย
                }
            },
            {
                data: null,
                render: function(data, type, row) {
                    let status = data.data_user.status;
                    let color_text = '';
                    if (status.startsWith('installment_')) {
                        const installmentNumber = status.split('_')[1];  // ดึงตัวเลขงวดจาก 'installment_1'
                        color_text = 'info';
                        text = `ชำระเงินงวดที่ ${installmentNumber}`;
                    } else if (status === 'completed') {
                        color_text = 'success';
                        text = 'จบโครงการ';
                    } else if (status === 'cancelled') {
                        color_text = 'danger';
                        text = 'ยกเลิก';
                    } else {
                        color_text = 'secondary';
                        text = 'สถานะไม่ทราบแน่ชัด';
                    }
                    return `<span class=" text-${color_text} mb-1">${text}</span>`;
                }
            },
            { 
                data: null,  

                orderable: false,  //ปิดการเรียงลำดับในคอลัมน์นี้
                render: function(data, type, row) {
                    const rowData = JSON.stringify(row).replace(/"/g, '&quot;'); 
                    return `
                    <a class="btn btn-danger btn-icon btn-circle " onclick="sweetAlertDel(${data.data_user.id})">
                        <i class="fas fa-trash"></i>
                    </a>                                           
                    <a href="javascript:;" onclick="sweetAlertReject('${data.data_user.id}','rejected')" hidden class=" btn btn-danger btn-icon btn-circle "><i class="fas fa-times"></i></a>
                    `;
                    
                }
            }
        ],
        order: [[0, "asc"]],  // เรียงลำดับจาก ID
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
        pageLength: 10
    });

    
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