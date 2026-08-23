document.addEventListener(
    "DOMContentLoaded",
    function () {

        const flashes =
            document.querySelectorAll(
                ".flash"
            );

        flashes.forEach(
            function (flash) {

                setTimeout(
                    function () {

                        flash.style.opacity = "0";

                        flash.style.transition =
                            "opacity 0.5s";

                        setTimeout(
                            function () {

                                flash.remove();

                            },
                            500
                        );

                    },
                    4000
                );

            }
        );

    }
);

document.addEventListener("DOMContentLoaded", function () {
    const roleSelect = document.querySelector("#role");
    const fields = document.querySelector("#athlete-coach-fields");

    if (!roleSelect || !fields) return;

    function updateFields() {
        const isScout = roleSelect.value === "scout";

        fields.hidden = isScout;

        fields.querySelectorAll("input").forEach(function (input) {
            input.disabled = isScout;
        });
    }

    roleSelect.addEventListener("change", updateFields);
    updateFields();
});