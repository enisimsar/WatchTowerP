$(document).ready(function () {
    $("#topic_dropdown").on('click', 'li a', function () {
        var selText = $(this).children("h4").html();
        $(this).parent('li').siblings().removeClass('active');
        $(this).parents('.btn-group').find('.selection').html(selText);
        $(this).parents('li').addClass("active");
    });

    $(window).scroll(function () {
        if ($("#spin").css("display") == "none" && $(window).scrollTop() + $(window).height() == $(document).height()) {
            var ncursor = 0;
            if($("#news > div").last().attr("cursor") != undefined) ncursor = $("#news > div").last().attr("cursor");
            if (ncursor != 0 && $('#newsDiv').length != 0) {
                $("#spin").show();
                var aid = $("#news").attr("alertid");
                var date = $('#newscontainer').attr("date");
                $.ajax({
                    url: '/News/scroll',
                    method: 'POST',
                    data: {
                        'next_cursor': ncursor,
                        'alertid': aid,
                        'date': date
                    },
                    success: function (html) {
                        $('#news').append(html);
                        $("#spin").hide();
                    }
                });
            }
        }
    });
});

$(document).ready(function () {
    $("#spin").spinner();
    $("#topic_dropdown").on('click', 'li a', function () {
        $('#newscontainer').empty();
        $("#spin").show();
        $("#date_buttons").show();
        var aid = $(this).attr("data-id");
        var date = 'yesterday';
        $('#newscontainer').attr("date", date);
        var children = $('#date_buttons').children();
        children.each(function () {
            if ($(this).attr('date') == date) {
                $(this).removeClass('btn-default');
                $(this).addClass('btn-success');
            } else {
                $(this).removeClass('btn-success');
                $(this).addClass('btn-default');
            }
        });
        $.ajax({
            url: '/News',
            method: 'POST',
            data: {
                'alertid': aid,
                'date': 'yesterday'
            },
            timeout: 10000,
            error: function () {
                $('#newscontainer').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
                $("#spin").hide();
            },
            success: function (html) {
                $('#newscontainer').empty();
                $('#newscontainer').append(html);
                $("#spin").hide();
            }
        });
    });
});

function getDate(date) {
    var aid = $("#news").attr("alertid");
    $("#spin").show();
    console.log(date);
    $('#newscontainer').attr("date", date);
    var children = $('#date_buttons').children();
    children.each(function () {
        if ($(this).attr('date') == date) {
            $(this).removeClass('btn-default');
            $(this).addClass('btn-success');
        } else {
            $(this).removeClass('btn-success');
            $(this).addClass('btn-default');
        }
    });
    $.ajax({
        url: '/News',
        method: 'POST',
        data: {
            'alertid': aid,
            'date': date
        },
        timeout: 10000,
        error: function () {
            $('#newscontainer').empty();
            $('#newscontainer').append("<p style='color: red; font-size: 15px'><b>Ops! We have some problem. Please, try again.</b></p>");
            $("#spin").hide();
        },
        success: function (html) {
            $('#newscontainer').empty();
            $('#newscontainer').append(html);
            $("#spin").hide();
        }
    });
}

function dummy(posttype, link_id) {
    $("#spin").show();
    var aid = $("#news").attr("alertid");
    $.ajax({
        url: '/bookmark',
        method: 'POST',
        data: {
            'alertid': aid,
            'posttype': posttype,
            'link_id': link_id
        },
        success: function (html) {
            if (posttype == 'add') {
                $('#'.concat(link_id).concat(' a span')).css('color', '#808080');
                $('#'.concat(link_id).concat(' a')).attr("onclick", "dummy('add', '".concat(link_id).concat("')"));
            } else {
                $('#'.concat(link_id).concat(' a span')).css('color', '#D70000');
                $('#'.concat(link_id).concat(' a')).attr("onclick", "dummy('remove', '".concat(link_id).concat("')"));
            }
            $("#spin").hide();
        }
    });
}

function sentiment(link_id) {
    var aid = $("#news").attr("alertid");
    var rating = $("#sentiment_".concat(link_id)).val();
    if(rating == "") rating = 0;
    $.ajax({
        url: '/sentiment',
        method: 'POST',
        data: {
            'alertid': aid,
            'rating': rating,
            'link_id': link_id
        },
        success: function (html) {
        }
    });
}

function ban_domain(domain) {
    $("#spin").show();
    var aid = $("#news").attr("alertid");
    $.ajax({
        url: '/domain',
        method: 'POST',
        data: {
            'alertid': aid,
            'domain': domain
        },
        success: function (html) {
            $("[domain='".concat(domain).concat("']")).remove();
            $("#spin").hide();
        }
    });
}
