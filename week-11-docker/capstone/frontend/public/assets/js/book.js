/* eslint-env jquery */
$(document).ready(function () {
  $(".modal").modal();
  $(".cart-button").on("click", function (event) {
    event.preventDefault();
    const button = $(this); button.prop("disabled", true);
    $.post("/api/cart", {bookId: Number(button.attr("value"))})
      .then(() => location.reload())
      .fail(() => { alert("The item could not be added. Please try again."); button.prop("disabled", false); });
  });
  $(".checkout-button").on("click", function (event) {
    event.preventDefault();
    const button = $(this); button.prop("disabled", true);
    $.post("/api/checkout", {})
      .then(data => {
        $("#checkout-result").text("Demo order saved. Order ID(s): " + data.orders.map(x => x.id).join(", ") + ". No payment was taken.");
        $("#checkout-modal").modal("open");
      })
      .fail(() => { alert("Checkout was not completed. Your cart is retained."); button.prop("disabled", false); });
  });
});
