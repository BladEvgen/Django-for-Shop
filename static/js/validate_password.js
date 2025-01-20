document.getElementById("password").addEventListener("input", function () {
  var password = this.value;
  var passwordStrength = document.getElementById("passwordStrength");
  var passwordHelp = document.getElementById("passwordHelp");
  var passwordTip = document.getElementById("passwordTip");
  var registerBtn = document.getElementById("registerBtn");

  passwordStrength.style.width = "0%";
  passwordStrength.classList.remove("bg-danger", "bg-warning", "bg-success");
  passwordHelp.textContent = "";
  passwordTip.textContent = "";

  var minLength = 8;
  var isLengthValid = password.length >= minLength;

  var conditions = [
    { regex: /[A-Z]/, fulfilled: false },
    { regex: /[a-z]/, fulfilled: false },
    { regex: /\d/, fulfilled: false },
    { regex: /[#!?@$%^&*-]/, fulfilled: false },
  ];

  conditions.forEach(function (condition) {
    condition.fulfilled = condition.regex.test(password);
  });

  var fulfilledConditions = conditions.reduce(function (count, condition) {
    return count + (condition.fulfilled ? 1 : 0);
  }, 0);

  var strength = (fulfilledConditions / conditions.length) * 100;

  if (!isLengthValid) {
    strength = 30;
  }

  if (strength < 33) {
    passwordStrength.classList.add("bg-danger");
    passwordHelp.textContent = "Weak password";
    passwordTip.textContent =
      "Для более надежного пароля используйте сочетание прописных и строчных букв, цифр и специальных символов (#?!@$%^&*-). Убедитесь, что его длина не менее 8 символов.";
    registerBtn.disabled = true;
  } else if (strength < 76) {
    passwordStrength.classList.add("bg-warning");
    passwordHelp.textContent = "Medium strength password";
    passwordTip.textContent =
          "Для более надежного пароля используйте сочетание прописных и строчных букв, цифр и специальных символов (#?!@$%^&*-). Убедитесь, что его длина не менее 8 символов.";
    registerBtn.disabled = true;
  } else {
    passwordStrength.classList.add("bg-success");
    passwordHelp.textContent = "Strong password";
    registerBtn.disabled = false;
  }

  passwordStrength.style.width = strength + "%";
});
