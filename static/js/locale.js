function changeLanguage(language) {
    document.cookie = "selected_language=" + language + "; expires=Thu, 31 Dec 2099 23:59:59 UTC; path=/";
    location.reload();
}
