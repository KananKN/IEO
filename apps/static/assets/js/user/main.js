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
            post("/setting/user/delete", { id: id });
        }
    });
}
function setEditValue(el,role_id) {

    const data = JSON.parse(el.dataset.user);

    $("#id-update").val(data.id);
    $('#username-update').val(data.username);
    $('#role_id-update').val(role_id);

    $('#first_name').val(data.first_name);
    $('#last_name').val(data.last_name);
    $('#phone').val(data.phone);
    $('#email').val(data.email);
    $('#bank_name').val(data.bank_name);
    $('#bank_account').val(data.bank_account);
}
// function setEditValue(id, username, role_id) {
//     // console.log(data);
//     $("#id-update").val(id);
//     $("#username-update").val(username);
//     // $("#password-update").val(data.password);
//     $("#role_id-update").val(role_id);
//     $("#role_id-update").val(role_id);
//     $("#first_name").val(role_id);
//     $("#last_name").val(role_id);
//     $("#phone").val(role_id);
//     $("#email").val(role_id);
//     $("#bank_name").val(role_id);
//     $("#bank_account").val(role_id);
// }
