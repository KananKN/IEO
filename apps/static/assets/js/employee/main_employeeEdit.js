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

function func_save() {
    // console.log("Saving...");

    $('#myForm').attr('action', '/sponsor/updateEmployee').attr('method', 'POST');
    $('#myForm').submit();
}

// let inputIds = [];

let inputIds = [];

$('#myForm').submit(function(e) {
    e.preventDefault(); // ป้องกันการ submit แบบปกติ

    let isValid = true;
   
    if (isValid) {
        // สามารถใช้บรรทัดนี้เพื่อส่งฟอร์มไปยัง backend:
        // $('#myForm').attr('action', route).attr('method', 'POST');
        this.submit(); // ทำการ submit ฟอร์มจริง
    }
});

function validateFile(input) {
    const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png']; // นามสกุลไฟล์ที่อนุญาต
    const file = input.files[0];

    if (file) {
        const fileExtension = file.name.split('.').pop().toLowerCase(); // ดึงนามสกุลไฟล์

        if (!allowedExtensions.includes(fileExtension)) {
            check_fail('อนุญาตให้เลือกเฉพาะไฟล์ PDF, JPG, JPEG, PNG เท่านั้น!');
            input.value = ''; // เคลียร์ค่า input
        }
    }
}
