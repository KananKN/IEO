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

function validateForm() {
    let isValid = true;

    // เช็คทุก input, textarea, select ที่ required
    $('#myForm').find('input[required], textarea[required], select[required]').each(function () {
        if (!$(this).val().trim()) {
            $(this).addClass('border-red-500');
            isValid = false;
        } else {
            $(this).removeClass('border-red-500');
        }
    });

    if (!isValid) {
        swal({
            icon: 'warning',
            title: 'กรุณากรอกข้อมูลให้ครบถ้วน',
        });
        return;
    }

    // ✅ ถ้าข้อมูลครบ เรียกฟังก์ชันบันทึก
    func_save();
}

// ฟังก์ชัน save
function func_save() {
    $('#myForm').attr('action', '/supplier/createMainSupplier').attr('method', 'POST');
    $('#myForm')[0].submit(); // ใช้ DOM submit โดยไม่ผ่าน event listener
}

// // Event handler ของฟอร์ม
// $('#myForm').submit(function(e) {
//     e.preventDefault();

//     if (validateForm()) {
//         func_save(); // เรียกเมื่อ valid แล้วเท่านั้น
//     }
// });

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
