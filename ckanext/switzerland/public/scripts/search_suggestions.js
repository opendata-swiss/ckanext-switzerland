$(function () {

  // Activate search suggestions for the search bar in the header and for the
  // search bar used in the body.
  $('#ogdch_search').autocomplete({
    delay: 250,
    html: false,
    minLength: 2,
    source: function (request, response) {
      var url = $('body').data('site-root') + '/api/3/action/ogdch_autosuggest';
      $.getJSON(url, {q: request.term, lang: $('html').attr('lang')})
        .done(function (data) {
          response(data['result']);
        });
      }
  });

})
