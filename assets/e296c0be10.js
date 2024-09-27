document.addEventListener("DOMContentLoaded", replaceDocsLinks);

function replaceDocsLinks() {
  const links = document.querySelectorAll("a[href]");

  links.forEach((link) => {
    let href = link.getAttribute("href");

    if (
      href.startsWith("https://docs.rememberizer.ai/") ||
      href.startsWith("https://docs.skydeck.ai/")
    ) {
      const url = new URL(href);
      const language = getLanguageFromURL();
      const newPath = `${url.origin}/v/${language}${url.pathname}`;
      link.setAttribute("href", newPath);
    }
  });
}

function getLanguageFromURL() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get("lang") || "en";
}
