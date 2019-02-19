$(document).ready(function() {
	$(".dropdown-menu li a").click(function(){
		$("#model").find('.selection').text($(this).text());
		$("#model").find('.selection').val($(this).text());
	});

	$("#search").click(function(){	
		submit();
	});
	
	$("body").keypress(function(event) {
	    if (event.which == 13) {
	    	event.preventDefault();
	        submit();
	    }
	});
});

function submit() {
	var $model = $("#model").find('.selection').text();
	var $query = $("#query").val();
	var $bodywgt = $("#bodywgt .active").text().trim();
	var $linkwgt = $("#linkwgt .active").text().trim();
	var $titlewgt = $("#titlewgt .active").text().trim();
	var $prwgt = $("#prwgt .active").text().trim();

	if($query == "")
		return;

	$.get( "searcher", { model: $model, query: $query, bodywgt: $bodywgt, linkwgt: $linkwgt, titlewgt: $titlewgt, prwgt: $prwgt } )
	.done(function( msg ) {
		try {
			console.log(msg);
			//var obj = JSON.parse(msg);

			var size = msg.size;
			//console.log(size);

			var time = parseFloat(msg.time); 
			var max = 10;

			if(size == 0){
				$("#stats_container > p").text("No results found");
				$("#result_container").html(""); 
				return;
			}
			else if(size == 1){
				$("#stats_container > p").text("1 result (" + time + " seconds)");
			}
			else if(size <= max){
				$("#stats_container > p").text(size + " results (" + time + " seconds)");
				max = size;
			}
			else {
				$("#stats_container > p").text("Showing top " + max + " results out of " + size + " found (" + time + " seconds)");
			}

			var html = "";
			for(var i=0; i<Math.min(max,size); i++){
				var title = msg.data[i].title; 
				var docid = msg.data[i].docid; 
				var url = decodeURIComponent(msg.data[i].url);
				html += "<div class='list-group'><h4 class='list-group-item-heading'>" + decodeURI(title) + "</h4><p class='list-group-item-text'><a href='http://" + url + "'>" + url + "</a> ("+docid+")</p></div>";
			}
			$("#result_container").html(html); 
			
			html = "";
			if(msg.eval['missing'] == -1){
				html += "<ul class='list-group'><strong>Query Not Evaluated</strong></ul>";
			}else{
				html += "<ul class='list-group'>";
				html += "<li class='list-group-item'><strong>Missing:</strong> <span class='badge'>" + msg.eval['missing'] + "</span></li>";
				html += "<li class='list-group-item'><strong>Precision:</strong> <span class='badge'>" + msg.eval['precision'] + "</span></li>";
				html += "<li class='list-group-item'><strong>Recall:</strong> <span class='badge'>" + msg.eval['recall'] + "</span></li>";
				html += "<li class='list-group-item'><strong>F1-Measure:</strong> <span class='badge'>" + msg.eval['f1'] + "</span></li>";
				html += "<li class='list-group-item'><strong>Average Precision:</strong> <span class='badge'>" + msg.eval['avg_prec'] + "</span></li>";
				html += "<li class='list-group-item'><strong>Reciporal Rank:</strong> <span class='badge'>" + msg.eval['rr'] + "</span></li>";
				html += "<li class='list-group-item'><strong>Normalized Discounted Cumulative Gain:</strong> <span class='badge'>" + msg.eval['ndcg'] + "</span></li>";
				html += "</ul>";
			}
			$("#eval_container > p").html(html) 

		} catch (e) {
			console.log(e.message);
			return showError();
		}
	}) 
	.fail(function() {
		return showError();
	}); 
}

function showError(){
	$("#stats_container > p").html("<strong>Oh sorry!</strong> Something isn't right!");
	$("#result_container").html("");
	return false;
}