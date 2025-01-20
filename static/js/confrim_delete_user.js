document.addEventListener("DOMContentLoaded", function () {
  const deleteButtons = document.querySelectorAll(".delete-btn");

  deleteButtons.forEach((button) => {
    button.addEventListener("click", function (event) {
      event.preventDefault();

      const username = button.getAttribute("data-username");
      const confirmation = prompt(
        `Чтобы подтвердить удаление, впишите CONFIRM и нажмите OK. Эти действия удалят пользователя "${username}".`
      );

      if (confirmation && confirmation.toUpperCase() === "CONFIRM") {
        window.location.href = button.getAttribute("href");
      } else {
        alert("Удаление отмененно.");
      }
    });
  });
});
