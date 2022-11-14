var containerEl=document.getElementById('progressbar-container');
infoEl= document.createElement('DIV')
infoEl.style.width='100%'
infoEl.style.display="flex"

document.getElementById('progress-container').prepend(infoEl)

dlInfoEl= document.createElement('P')
dlInfoEl.innerText= 'Initializing download...'
dlInfoEl.style.display="inline-block"
infoEl.appendChild(dlInfoEl)

dlPercentEl= document.createElement('P')
dlPercentEl.innerText= '0%'
dlPercentEl.style.display="inline-block"
dlPercentEl.style.marginLeft="auto"
infoEl.appendChild(dlPercentEl)


progressEl= document.createElement('DIV')
progressEl.style.width='2%'
progressEl.style.minHeight=containerEl.style.minHeight;
progressEl.style.backgroundColor="#3a5887"

containerEl.appendChild(progressEl)





function changeProgress(data){
	if(data['all_done']){
		data['all_done']=false
		changeProgress(data)
		document.getElementById('downloadLinks').hidden=false;
		

		return dlInfoEl.innerText= "File is ready for download.";
	}
	if(data['video_downloaded'] && data['audio_downloaded'])
		dlInfoEl.innerText= "Merging Files...";
	else
		dlInfoEl.innerText= "Downloading " +data['filetype']+" file...";
	var percent= data['downloaded_bytes']/data['total_bytes']*100
	progressEl.style.width= Math.ceil(percent)+'%';

	dlPercentEl.innerText=Math.ceil(percent)+'%'
}


var prev_req_time= new Date().getTime()
var identifier= window.location.href.split('?')[0].split('/').slice(-1)[0]
var wait_time= 1000
function getData(){
	fetch('/progress/'+identifier).then(function(res){ return res.json() }).then(function(data){
		if(!data) {
			var time_passed=new Date().getTime()-prev_req_time;
			prev_req_time= new Date().getTime();

			return setTimeout(getData, wait_time-time_passed);
		}
		var time_passed=new Date().getTime()-prev_req_time;
		prev_req_time= new Date().getTime();
		
		changeProgress(JSON.parse(JSON.stringify(data)))
		if ( data['all_done'] ) return;

		if ( time_passed < wait_time ){
			setTimeout(getData, wait_time-time_passed)
		} else {
			getData()
		}
	})
	
	
}

getData()

