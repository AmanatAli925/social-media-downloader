from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import urllib
import yt_dlp
import yt_dlp.utils
import json
from signal import *
import sys, time
import atexit
import random
import string
import threading

WORKING_DIR= '/home/ubuntu/video_downloader/downloader'
YOUTUBE_COOKIE_FILE= '/home/ubuntu/youtube/youtube.com_cookies_type.txt'
FACEBOOK_COOKIE_FILE= ''
INSTAGRAM_COOKIE_FILE= ''
FORMATS_FILE_LOC='/home/ubuntu/video_downloader/downloader/formats_.txt'
F_SEPARATOR='+'

sites = [ 'youtube', 'facebook', 'tiktok', '23video', '56.com']

formats_= open(FORMATS_FILE_LOC, 'r').read().strip()			# formats that need further processing
formats_=  json.loads(formats_) if formats_  else {}
progresses={}

def dump_formats(*args, exit=False):
	open(FORMATS_FILE_LOC, 'w+').write(json.dumps(formats_))
	sys.exit(0)

for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM, SIGUSR1):
	signal(sig, dump_formats)

atexit.register(dump_formats)


def random_str(n):
	return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(n))



def yt_dlp_instance(options):
	yt_dlp.utils.std_headers['User-Agent'] = options['user-agent']
	yt_dlp_opts= {
			'noplaylist': True,
			'geo_bypass': True
			
		}
	try:
		yt_dlp_opts['cookiefile']=eval(options['site'].upper()+'_COOKIE_FILE')
	except:
		pass
	return yt_dlp.YoutubeDL(yt_dlp_opts)
	


def yt_videos_filter(videos):
	temp=[]

	#priorites mp4s
	videos= list(filter(lambda v: v['video_ext'].lower()=='mp4', videos))+list(filter(lambda v: v['video_ext'].lower()=='webm', videos))
	#'height' in video and v['height']==video['height']
	for video in videos:
		#if not height known, then add it anyway ( to be on safe side )
		if not 'height' in video:
			temp.append(video)			
			continue
		#if mp4 video with same height already exists
		if [v for v in temp if 'format_note' in video and 'height' in v and v['height']==video['height']]:	
			continue
		#if not then append it not matter what format it is
		else:
			temp.append(video)			


	return temp



def process_info(info, options):
	audios=[]
	videos=[]
	if options['site'] == '56':
		for format in info['formats']:
			format['vcodec']= 'mp4'		# hardcoding vcodec and acodec bcz video are in simple mp4 formats
			format['acodec']= 'm4a'
			format['format']= 'mp4'
	
	only_directs=options['site']=='9now'
	
	print('only directs is ', only_directs)
	for format in info['formats']:
		
		if 'ytimg' in format['url'] or not 'vcodec' in format:	# if image or does not contain 'vcodec' (used in below code) then continue
			
			continue
		# if only directs are required, then check that audio must exist with video
		if only_directs and (not 'acodec' in format or format['acodec'].lower()=='none'):
			continue
		if  format['vcodec'].lower()=="none":
			audios.append(format)
		else:	
			videos.append(format)
	
	videos=yt_videos_filter(videos)
		
	return {'audios': audios, 'videos': videos}
def get_file_size(bytes):
	units={
		'Kb': 1024,
		'Mb': 1024 * 1024,
		'Gb': 1024 * 1024 * 1024,
		'Tb': 1024 * 1024 * 1024 * 1024
	}
	
	size= str(bytes)+' Bytes'
	for key, unit in units.items():
		if unit/bytes > 1:
			break
		size= "{:.1f}".format(bytes/unit) +' '+ key
	return size

def get_facebook_urls(options):
	return get_youtube_urls(options)


def get_tiktok_urls(options):
	return get_youtube_urls(options)

def get_youtu_urls(options):
	return get_youtube_urls(options)

def get_23video_urls(options):
	return get_youtube_urls(options)

def get_56_urls(options):
	return get_youtube_urls(options)
def get_9now_urls(options):
	return get_youtube_urls(options)


def get_academicearth_urls(options):
	return get_youtube_urls(options)

def get_youtube_urls(options):

	ytdlp= yt_dlp_instance(options)
	
	info=ytdlp.extract_info(options['uri'], download=False)
	open('/home/ubuntu/video_downloader/downloader/info.txt', 'w+').write(json.dumps(info, indent=4))
	
	#if formats in entries array then put them globally.
	if 'entries' in info:
		info['formats']= info['entries'][0]['formats']
	#if no formats in info, then no need to process the info	
	if not 'formats' in info:
		return [{
			'link': info['url'],
			'text': 'Video Downloadable directly'
		}]
	processed_info=process_info(info, options)
	# if there is a video without audio
	key= random_str(20)
	downloadUrls=[]
	
	for video in processed_info['videos']:
		size=""
		if 'filesize' in video and video['filesize']:
			size= ' ['+get_file_size(video['filesize'])+'] '
		video['format_note']= video.get('format_note', '')
		if 'throttle' in video['format_note'].lower():
			continue
		
		# if video only, add to formats that need processing
		if 'acodec' in video and video['acodec'].lower()=='none':
			#formats_[key+'-info']=info
			info['audios']=processed_info['audios']
			height=''
			if 'height' in video and video['height']:
				height=str(video['height'])+'p'
			downloadUrls.append({ 
				'link': '/process/'+key+F_SEPARATOR+video['format_id'], 
				'text': height+' Video'+size+ ' (Need processing)'
			})
		# append direct downloadLink  
		elif not ( 'hls' in video['format'].lower() or 'dash' in video['format'].lower()):
			height=''
			if 'height' in video and video['height']:
				height=str(video['height'])+'p'

			downloadUrls.append({
				'link': video['url'],
				'text': height + ' Video'+size+ ' (Downloadable directly)'
			})
	#open(FORMATS_FILE_LOC, 'w+').write(json.dumps(formats_))
	
	open(WORKING_DIR +'/'+key+'-info', 'w+').write(json.dumps(info))

	return downloadUrls


def progress_hook(temp):
	if not 'key' in temp['info_dict']:
		return False
	key=temp['info_dict']['key']
	
	video_id= temp['info_dict']['key'].split(F_SEPARATOR)[1]
	filetype = 'video' if temp['filename'].split('.')[-2]== 'f'+video_id else 'audio'
	temp['filetype']=filetype 
	temp['audio_downloaded']= progresses.get(key, {}).get('audio_downloaded', False)
	temp['video_downloaded']= progresses.get(key, {}).get('video_downloaded', False)
	if temp['status']=='finished':
		temp[filetype+'_downloaded']=True
	
	progresses[key]= temp
	#old_temp=open(WORKING_DIR +'/temp', 'r').read()
	#open(WORKING_DIR +'/temp', 'w+').write(old_temp+'\n\n\n\n'+json.dumps(temp, indent=4))


def download_video(audio_id, video_id, key, final_ext):
	yt_dlp_opts={ 
		'format': str(audio_id)+'+'+str(video_id),
		'merge_output_format': final_ext, 
		'progress_hooks': [progress_hook],
		'outtmpl': '/mnt/disk1/video_downloader/videos/'+key+F_SEPARATOR+video_id+'.%(ext)s',
		'noprogress': True
	
	}
	with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl: 
    		error_code = ydl.download_with_info_file(WORKING_DIR+'/'+key+'-info')
	if key+F_SEPARATOR+video_id in progresses:
		progresses[key+F_SEPARATOR+video_id]['all_done']=True 
	
	
def progress(request, identifier):	
	return JsonResponse(progresses.get(identifier, {}))



def process(request, identifier):
	audio= request.GET.get('audio', '')
	if not audio:
		return render(request, 'process.html', {
			'audioSelect': not audio
		}) 
	
	
	video_id= identifier.split(F_SEPARATOR)[1].strip()
	
	key= identifier.split(F_SEPARATOR)[0]

	info= json.loads(open(WORKING_DIR+'/'+key+'-info', 'r').read()) 
	video=[ v for v in info['formats'] if 'format_id' in v and v['format_id']==video_id ][0]
	video_ext= video['video_ext']
	print('video ext is ', video_ext)
	audio_ext= 'm4a' if video_ext=='mp4' else 'webm'
	#print(info['audios'])

	audios= [ a for a in info['audios'] if 'audio_ext' in a and a['audio_ext']==audio_ext ]
	
	#if no audio found with matching video format, then choose other anyway
	if not audios:
		audios= info['audios']
		video_ext= 'mkv'
		

	if audio=='low':
		audio=0
	if audio=='medium':
		audio=len(audios)//2
	if audio=='high':
		audio=len(audios)-1

	audio_id= audios[audio]['format_id'] 
	#open(WORKING_DIR +'/new_temp', 'w+').write(json.dumps({ 'audios': audios, 'video':video}, indent=4))
	
	info['key']= key+F_SEPARATOR+video_id
	open(WORKING_DIR +'/'+key+'-info', 'w+').write(json.dumps(info))

	dl_thread= threading.Thread(target=download_video, args=(audio_id, video_id, key, video_ext))
	dl_thread.start()
	return render(request, 'process.html',  {
		'audioSelect': not audio,
		'filename': key+F_SEPARATOR+video_id+'.'+video_ext,
		'F_SEPARATOR':F_SEPARATOR
	})

def robotstxt(request):
	return HttpResponse('')

def bingxml(request):
	return render(request, 'BingSiteAuth.xml', {"foo": "bar"}, content_type="application/xhtml+xml")


def index(request, site=False):
	sites_start=0
	sites_end=3
	
	if site:
		print('site is ', site)
		sites_start=sites.index(site)
		sites_end= sites_start+1
	
	uri_arg_keyword='uri'
	full_path=request.get_full_path() 
	uri_arg_loc= full_path.find(uri_arg_keyword+'=')
	if uri_arg_loc==-1:
		return render(request, 'downloader.html', {
			'sites': ', '.join(sites[sites_start:sites_end]),
			'all_sites': ', '.join(sites)

		})
		
	
	try:
		uri= urllib.unquote(full_path[ uri_arg_loc+len(uri_arg_keyword)+1: ])		# python 2 
	except:
		uri= urllib.parse.unquote(full_path[ uri_arg_loc+len(uri_arg_keyword)+1: ])	# python 3
	
	try:
		site= '.'.join(uri.split('/')[2].split('.')[-2:])
		site.split('.')[1]		# testing that site name is at least two words long i.e "youtube and com"
	except:
		return render(request, 'downloader.html', { 'error_message' : 'Invalid Url!', 'uri': uri} )
	
	if uri.split('/')[2].endswith('9now.com.au') and not site:
		site='9now.com'
	downloadUrls=[]
	
	options={
		'uri': uri,
		'user-agent': request.headers['User-Agent'],
		'site': site.split('.')[-2]
	}
	
	try:
		downloadUrls=eval('get_'+site.split('.')[-2]+'_urls')(options)	
	except Exception as e:
		print('EXCEPTION OCCURED ', e)
		return HttpResponse('Sorry some thing went wrong.')

				
	return render(request, 'downloader.html', { 
			'uri': uri, 
			'downloadLinks': downloadUrls, 
			'sites': ', '.join(sites[sites_start: sites_end]),
			'all_sites': ', '.join(sites)
	})


