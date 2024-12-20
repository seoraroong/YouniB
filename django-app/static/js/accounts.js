document.addEventListener("DOMContentLoaded", function () {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const forms = document.querySelectorAll(".form");

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", function () {
            const target = this.dataset.target;

            // Update active tab
            tabButtons.forEach((b) => b.classList.remove("active"));
            this.classList.add("active");

            // Show/hide forms
            forms.forEach((form) => {
                form.classList.remove("active");
                if (form.id === target.substring(1)) {
                    form.classList.add("active");
                }
            });
        });
    });
});
