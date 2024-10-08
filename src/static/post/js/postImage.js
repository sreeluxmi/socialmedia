document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("imagePostingForm").addEventListener("submit", function (event) {
        event.preventDefault()
        var access_token = localStorage.getItem('access_token')

        if (access_token){
            const imageInput = document.getElementById("images");
            const captionInput = document.getElementById("caption");
    
            const formData = new FormData();
            const images = imageInput.files;
    
            if (images.length > 0) {
                for (let i = 0; i < images.length; i++) {
                    formData.append("uploaded_images", images[i]);
                }
            } else {
                formData.append("uploaded_images", imageInput.files[0]);
            }
            
            formData.append("caption", captionInput.value);

            for (const value of formData.values()) {
            console.log(value);
            }

    
            fetch("/apps.post/api/posts/", {
                method: "POST",
                headers: {
                    "Authorization" : "Bearer " + access_token
                },
                body: formData,
            })
            .then(function (response){
                if (response.ok){
                    console.log("success")
                    window.location.href = '/users/me/'
                }else{
                    console.log("Error")
                }
            })
        }else{
            window.location.href = '/users/home/';
        }

    });
});
