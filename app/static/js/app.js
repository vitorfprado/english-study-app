document.body.addEventListener("htmx:afterSwap", function (evt) {
  if (evt.detail.target && evt.detail.target.id === "answer-result") {
    evt.detail.target.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
});
