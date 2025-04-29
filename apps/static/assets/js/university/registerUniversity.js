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


function func_save(){
    const form = document.getElementById("myForm"); // ✅ ใช้ ID ของ form
    const formData = new FormData(form);
    console.log("save")
    fetch("/university/create_university_api", {
          method: "post",
          body: formData
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
                    location.reload();
                    // window.location.href = "/waiting_approval";
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

 if (window.history.replaceState) {
      window.history.replaceState(null, null, window.location.href);
}