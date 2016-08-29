(function($) {
    $(function() {
	    Thunder.connect(
	    	THUNDERPUSH_HOST,
	    	THUNDERPUSH_APIKEY,
	    	['cards', 'products'],
	    	{
	    		log: true,
	    		protocol: THUNDERPUSH_PROTO
	    	}
	    );

        Thunder.listen(function(data, channel) {
            $('*[subscribed-to=' + channel + ']').trigger({
                'type': 'scan', 'scannedData': data
            });
        });

        if (document.querySelector('#scan-card')) {
            var l = Ladda.create(document.querySelector('#scan-card'));

            $('#scan-card').click(function(e) {
                e.preventDefault();

                // start spinning
                l.start();

                // await a card number
                var url = $(this).attr('href').slice(0, -1);

                $(this).attr('subscribed-to', 'cards');
                $(this).on('scan', function(data) {
                    document.location = url + data.scannedData;
                    $(this).off('scan');
                });

                // disable the button
                $('#scan-card').off('click').click(function(e) {
                    e.preventDefault();
                });
            });
        }

        $('body').delegate('.scan-btn', 'click', function(e) {
            e.preventDefault();

		    var l = Ladda.create(this);
            var that = this;
            var input = $(that).parents('.form-row').find('input[scanner]');

            if (l.isLoading())
                return;

            l.start();

            $(this).attr('subscribed-to', input.attr('scanner'));
            $(this).on('scan', function(data) {
                $(this).off('scan');
                input.val(data.scannedData);
                l.remove();
            });
        });
    });
})(django.jQuery);;
