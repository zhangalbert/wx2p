$(document).ready(function() {

	var host = window.location.host;

	var ws = new ReconnectingWebSocket('wss://' + host + '/ws');
	ws.debug = true;
	ws.timeoutInterval = 3000;

	var $message = $('#ws_status');

	tbl = $('#eventList').DataTable({
		"columnDefs": [{"targets":0, "visible": false}, {"targets":1, "width":"20%"}, 
					   {"targets":2, "width":"20%"},{"targets":3, "width":"40%"},{"targets":4, "visible": false},{"targets":5, "width":"10%"},
					   {"targets":-1, "width":"10%", "data":null, "defaultContent": '<button class="btn btn-danger btn-xs">删除</button>'}],
		"order": [[ 1, "desc" ]],
		"oLanguage": {"sEmptyTable": "暂无告警信息"},
		"rowCallback": function(row, data, index) {
			if (data[4] == '5' || data[4] == '4') {
				$('td', row).css('background-color', 'Red');
			}
			if (data[4] == '3') {
				$('td', row).css('background-color', 'Orange');
			}		
		}
	});

	ws.onopen = function() {
		$message.attr("class", 'label label-success');
		$message.text('open');
	};

	ws.onmessage = function(ev) {
		$message.attr("class", 'label label-info');
		$message.text('recieved message');

		$message.fadeIn("slow");

		data = JSON.parse(ev.data);
		if (data.status == 1) {
			fnDeleteRows(tbl, data.eventid)
		}else{
			tbl.row.add([data.eventid, data.dt, data.host, data.content, data.severity, data.duration]).draw( false );
			if (data.is_sound == 1){
				audio4new(data);
			}
			// responsiveVoice.speak("收到新的告警 请查看", "Chinese Female");
		}
		$message.text('waiting message');
	}

	$('#eventList tbody').on( 'click', 'button', function () {
		var tr = tbl.row( $(this).parents('tr') )
		var tdata = tr.data();
		$.ajax({
			url: "/pushAlert",
			data: {eventid: tdata[0]},
			type: "post",
			dataType: "json",
			success: function(data){
				if (data.errCode == 0){
					tr.remove().draw();
				}else{
					alertDiag(data.errMsg);
				}
			}	
		});
	});

	ws.onclose = function(ev) {
		$message.attr("class", 'label label-important');
		$message.text('closed');
	}

	ws.onerror = function(ev) {
		$message.attr("class", 'label label-warning');
		$message.text('error occurred');
	}

	
	$.ajax({
		url: "/pushAlert",
		type: "get",
		dataType: "json",
		success: function(data){
			for (var i = 0; i < data.length; i++){
				var d = data[i]
				tbl.row.add([d.eventid, d.dt, d.host, d.content, d.severity, d.duration]).draw(false);
			}	
		}		
	});

	var fnDeleteRows = function (table, eventid){
		var indexes = table.rows().eq( 0 ).filter( function (rowIdx) {
			return table.cell( rowIdx, 0).data() == eventid ? true : false;
		});

		table.rows(indexes).remove().draw();
	}

	var audio4new = function(data){
		var text = "收到新的告警请查看";
		text = encodeURI(text);
		
		var s = '<audio autoplay="autoplay">';
		s += '<source src="https://tsn.baidu.com/text2audio?lan=zh&ctp=1&per=0&cuid=1&tok='+ data.tok +'&tex='+ text +'"  type="audio/mpeg">';
		s += '<embed height="0" width="0" src="http://tsn.baidu.com/text2audio?lan=zh&per=0&ctp=1&cuid=1&tok='+ data.tok +'&tex='+ text+'">';
		s += '</audio>';
		
		$("#audio4new").html(s);
	}

	var alertDiag = function(data) {
		$("#modal-alert-text").text(data);
		$('#modal-alert').modal('show');
	};

	var _s = function(s) {
		totalSeconds = s;
		var days = Math.floor(totalSeconds / 86400);
		totalSeconds %= 86400;
		var hours = Math.floor(totalSeconds / 3600);
		totalSeconds %= 3600;
		var minutes = Math.floor(totalSeconds / 60);
		seconds = totalSeconds % 60;

		if (days > 0){
			return days+'d'+hours+'h'+minutes+'m'+seconds+'s';
		}
		if (hours > 0){
			return hours+'h'+minutes+'m'+seconds+'s';
		}
		if (minutes > 0){
			return minutes+'m'+seconds+'s';
		}
		return seconds+'s';
	}

	var duration = function() {
		tbl.rows().every(function(rowIdx, tableLoop, rowLoop){
			var d = this.data();
			var now_ts = parseInt((new Date()).valueOf()/1000);
			var happen_ts = Math.round(new Date(d[1]).getTime()/1000);
			var gap = now_ts - happen_ts;
			var gap_str = _s(gap);
			d[5] = gap_str;
			this.invalidate();			
		});
		tbl.draw();
	}

	var timer = setInterval(function() {
		duration();
	}, 5000);
});
