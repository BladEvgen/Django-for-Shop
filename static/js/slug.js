document.addEventListener("DOMContentLoaded", function () {
  function transliterate(text) {
    const translitMap = {
      а: "a",
      б: "b",
      в: "v",
      г: "g",
      д: "d",
      е: "e",
      ё: "yo",
      ж: "zh",
      з: "z",
      и: "i",
      й: "y",
      к: "k",
      л: "l",
      м: "m",
      н: "n",
      о: "o",
      п: "p",
      р: "r",
      с: "s",
      т: "t",
      у: "u",
      ф: "f",
      х: "kh",
      ц: "ts",
      ч: "ch",
      ш: "sh",
      щ: "shch",
      ы: "y",
      э: "e",
      ю: "yu",
      я: "ya",
      ь: "",
      ъ: "",
      " ": "-",
      "—": "-",
      _: "-",
      ".": "",
      ",": "",
    };

    return text
      .toLowerCase()
      .split("")
      .map((char) => translitMap[char] || char)
      .join("")
      .replace(/[^a-z0-9\-]/g, "") // Удалить недопустимые символы
      .replace(/--+/g, "-") // Устранить двойные дефисы
      .replace(/^-+|-+$/g, ""); // Удалить дефисы в начале и конце
  }

  const titleInput = document.querySelector("input[name='title']");
  const slugInput = document.querySelector("input[name='slug']");

  titleInput.addEventListener("input", function () {
    slugInput.value = transliterate(titleInput.value);
  });
});
