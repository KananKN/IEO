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
            post("/setting/role/delete", { id: id });
        }
    });
}



function setEditValue(roleData, rolePermissions){

    console.log(roleData)
    console.log(rolePermissions)
    // ใส่ role id
    document.getElementById('role_id').value = roleData.id

    // เคลียร์ checkbox ทั้งหมดก่อน
    document.querySelectorAll('.perm-checkbox')
        .forEach(cb => cb.checked = false)

    // ดึง permission id ของ role นี้
    const permIds = rolePermissions.map(p => p.id)

    // ไล่ติ๊ก checkbox ให้ตรง
    document.querySelectorAll('.perm-checkbox')
        .forEach(cb => {
            if (permIds.includes(parseInt(cb.value))){
                cb.checked = true
            }
        })
}
// function setEditValue(data, data2) {
//     console.log(data2);
//     $("#id-update").val(data.id);
//     $("#name-update").val(data.name);
//     $("#description-update").val(data.description);
//     $(`.permission-update`).prop("checked", false);
//     data2.forEach((d) => {
//         $(`#permission-update_${d.id}`).prop("checked", true);
//     });
// }

$('#modal-dialog').on('show.bs.modal', function () {

    $(this).find('form')[0].reset(); // reset input ทั้งหมด
    $(this).find('.perm-checkbox').prop('checked', false); // reset checkbox

});