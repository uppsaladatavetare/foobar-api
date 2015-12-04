(function($) {
    $(function() {
        if (!document.querySelector('#scan-card'))
            return;

        var l = Ladda.create(document.querySelector('#scan-card'));

        $('#scan-card').click(function(e) {
            e.preventDefault();

            // start spinning
            l.start();

            // await a card number
            var url = $(this).attr('href').slice(0, -1);

            Thunder.connect(
                THUNDERPUSH_HOST,
                THUNDERPUSH_APIKEY,
                ['cards'],
                {
                    log: true,
                    protocol: THUNDERPUSH_PROTO
                }
            );

            Thunder.listen(function(data) {
                document.location = url + data;
            });

            // disable the button
            $('#scan-card').off('click').click(function(e) {
                e.preventDefault();
            });
        });
    });
})(django.jQuery);;
