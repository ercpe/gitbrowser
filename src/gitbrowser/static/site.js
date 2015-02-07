$(document).ready(function() {
	$('a.clone-protocol').on('click', function(e) {
		e.preventDefault();
		$('#clone-url').attr('value', $(this).data('url'));
		$('#clone-protocol').text($(this).text());
	});

	$('#clone-url').on("click", function () {
		$(this).select();
	});
});