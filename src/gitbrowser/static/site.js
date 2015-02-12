$(document).ready(function() {
	$('a.clone-protocol').on('click', function(e) {
		e.preventDefault();
		$('#clone-url').attr('value', $(this).data('url'));
		$('#clone-protocol').text($(this).text());
	});

	$('#clone-url').on("click", function () {
		$(this).select();
	});

	if ($('body').width() >= 450) {
		$('.tree-table').each(function(idx, table) {
			var ev = new EventSource($(table).data('url'));
			ev.onmessage = function(e) {
				var data = JSON.parse(e.data);
				$('#commit_' + data['obj']).html(data['summary_link']);
				$('#datetime_' + data['obj']).html(data['commit_datetime']);
			};
			ev.onerror = function(e) {
				ev.close();
			};
		});
	}
});