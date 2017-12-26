$(function(){
	$("#commit").on('click', function(){
		var event_id = $("#event_id").val();
		var ps = $("#sel").val();

		$.ajax({
			url: "/issue/"+event_id,
			type: "post",
			data: {process_status: ps},
			dataType: "json",
			success: function(data){
				if (data.errCode == 0){
					alert("提交成功");
				}else{
					alert(data.errMsg);
				}
			}			
		});	
	});
});
