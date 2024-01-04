from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from pydub import AudioSegment
import os
import uuid
import pandas as pd
from moviepy.editor import VideoFileClip
from google.cloud import storage
from google.cloud import speech_v1p1beta1 as speech
from google.protobuf.json_format import MessageToJson
import json
from konlpy.tag import Okt
from konlpy.tag import Kkma
from collections import Counter
import torch

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import concurrent.futures
from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration

# AudioSegment.converter = "C:/ffmpeg-6.1-essentials_build/ffmpeg-6.1-essentials_build/bin"




def makeFileName(ext):
    filename = f"file_{uuid.uuid4()}."+ ext
    return filename

def makeFolderName():
    foldername = f"folder_{uuid.uuid4()}"
    return foldername




def responseToSpring(request):
    try:
        folder_dir = request.GET.get('folder_dir')
        fileName = request.GET.get('fileName')
        flac_dir = videoToAudio(folder_dir, fileName)
        audio_paths = split_flac(flac_dir, folder_dir, 30)
        result = transcribe_audio_parallel(audio_paths)
        deleteUsedLocalFiles(flac_dir, audio_paths)
        return JsonResponse(result)
        
    except Exception as e:
        print(str(e))
        return HttpResponse(f"error :{e}")
    


# def responseToSpring(request):
#     try:
#         folder_dir = request.GET.get('folder_dir')
#         fileName = request.GET.get('fileName')
        
#         print(folder_dir)
#         print(fileName)
        
#         flac_dir = videoToAudio(folder_dir,fileName)
#         gcs_fileName = makeFileName('flac')
#         bn =upload_file_to_gcs(flac_dir,gcs_fileName)
#         flacInGCS = "gs://audio_storage_tpj/"+bn
#         result = transcribe_audio(flacInGCS)
#         deleteUsedLocalFile(flac_dir)
#         deleteUsedGCSFile(gcs_fileName)
        
#     except Exception as e:
#         print(str(e))
#         return HttpResponse(f"error :{e}")
    
#     return JsonResponse(result)



def videoToAudio(folder_dir,video_file_name):
    
    try:
        video_dir = folder_dir + video_file_name

        mp3_name = makeFileName('mp3')
        flac_name = makeFileName('flac')
        mp3_dir = folder_dir + mp3_name
        flac_dir = folder_dir + flac_name
        
        with VideoFileClip(video_dir) as video_clip:
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(mp3_dir, codec='mp3')
        
        print('-'*50)
        
        audio_segment = AudioSegment.from_mp3(mp3_dir)
        audio_segment.export(flac_dir, format='flac')
        
        os.remove(mp3_dir)
        
        return flac_dir
        
    except Exception as e:
        print("error : "+str(e))
    return flac_dir



def upload_file_to_gcs(local_file_path, outputFileName):
# 구글 클라우드 스토리지(gcs)에 오디오파일(flac) 업로드
    bucket_name = 'audio_storage_tpj'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob("audio/"+outputFileName)
    blob.upload_from_filename(local_file_path)
    print(blob.name)
    
    return blob.name



def transcribe_audio(flacInGCS):
    
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=flacInGCS)
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        language_code="ko-KR",
        enable_word_time_offsets=True,
        sample_rate_hertz=44100,
        audio_channel_count=2,
    )
    
    operation = client.long_running_recognize(config=config, audio=audio)
    print("Waiting for operation to complete")
    response = operation.result()
    
    transcript = ""
    words = []

    for result in response.results:
        transcript += result.alternatives[0].transcript
        words += result.alternatives[0].words

    tandw = []

    for w in words:
        word = {}
        word['word'] = w.word
        word['start'] = w.start_time.seconds
        tandw.append(word)
        
    
    topWords = get_top_words(transcript)
    
    return {"transcript": transcript, "words":tandw, "topWords":topWords}
    


def get_top_words(transcript):
    okt = Okt()
    morphs = okt.pos(transcript)  # 형태소 분석 수행
    stop_word = "가까스로 가령 각 각각 각자 각종 개 의치 거바 거의 것 것 것 게다가 겨우 견지 결과 결론 낼 수 겸사겸사 고려 고로 곧 공동 과 과연 관계 관련 관 관 관 구 구체 구토 그 그 그때 즉 까닭 즉 불구 함 만이 그 위 중 근거 근거 기대 기점 기준 기타 까닭 끙끙 끼익 나 나머지 남 남짓 너 너희 너희 네 넷 년 논 누가 누구 다른 다른 방면 다만 다섯 다소 다수 다시 말 다음 다음 다음 단지 답 당신 당장 대로 대하 대하 대해 말 대해 댕그 더구나 더군다나 더라도 더욱더 더욱이 도달 도착 동시 동안 바 이상 두번째 둘 둥둥 뒤 간 등 등등 딩동 따라서 따위 때 때 때문 또 또한 뚝뚝 해도 령 로 로 로부터 로써 륙 를 마음대로 마저 마치 막론 만 만약 만약 만일 만큼 말 말 매 매번 메 겁 몇 모 모두 무렵 무릎 무슨 무엇 무엇 때문 및 말 말 바로 바 반대 반대 말 반드시 버금 더 보드득 본대 부류 사람 부터 불구 불문 붕붕 비걱거리 비교 비로소 비록 보아 비 뿐 뿐 뿐 삐걱 삐걱 거리 사 삼 상대 말 생각 대로 설령 설마 설사 셋 소생 소인 솨 쉿 시각 시간 시작 시초 실로 심지어 아래 윗 거나 아무 아야 아이 아이야 아하 아홉 안 위 위해 알 수 앗 앞 앞 것 약간 양자 어기 차 년도 것 곳 때 쪽 해 어디 것 어이 어째서 어쨋 수 어찌 어찌됏 어찌 됏 어찌 어찌하여 언제 얼마 얼마 안 것 얼마간 얼마나 얼마 얼마만큼 얼마 엉엉 대해 여 여기 여덟 여러분 여보 시오 여부 여섯 차 연관 이서 영 영차 옆 사람 예 예 예 예 오 오르다 자마자 오직 오히려 사람 와르르 왜 외 요 것 걸 요컨대 우르르 우리 우리 우선 우 종합 것과 월 위 서술 바 위 위해 윙윙 육 응 응당 의 의거 의지 이 이 이 때문 이 이 외 이 정도 것 곳 때 라면 정도 것 이로 리하 이 이번 이 이상 이 이 이 반대 이 이외 이용 이유 젠 쪽 이천구 이천육 이천칠 이천팔 인 듯 인젠 일 일곱 일단 때 일반 일지 임 입 각하 입장 자 자기 자기 집 자마자 자신 잠깐 잠시 저 것 것 저기 저쪽 저희 전부 전자 전후 점 보아 정도 제 제각기 제외 조금 조차 졸졸 좀 좍좍 주룩주룩 주저 줄 몰랏다 줄 중 중 하나 즈음 즉 즉시 진짜 쪽 차라리 참나 첫 적 적 말 적 칠 콸콸 쿵 타인 토 통 툭 퉤 팍 팔 퍽 펄렁 곤 때문 위 하나 김 편이 낫다 낫다 바 하든 하물며 하자 마자 하하 까닭 이유 후 한마디 한적 항목 따름 생각 줄 지경 힘 때 만하 망정 뿐 알다 해도 해도 해 향 향 향 허걱 형식 혹시 혼자 휘익 흐흐 흥 힘"
    sw = set(stop_word.split(" "))
    
    eojeols = [morph[0] for morph in morphs if morph[1] == 'Noun' and morph[0] not in sw]

    top_words = Counter(eojeols).most_common(3)
    return top_words



def deleteUsedLocalFiles(audio_file_path,audio_paths):
    print("deleteUsedLocalFile")
    print(audio_file_path)
    os.remove(audio_file_path)
    for audio_path in audio_paths:
        os.remove(audio_path)
        

def deleteUsedLocalFile(audio_file_path):
    print("deleteUsedLocalFile")
    print(audio_file_path)
    os.remove(audio_file_path)
    
    
   
   
def deleteUsedGCSFile(gcs_fileName):
    bucket_name = 'audio_storage_tpj'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob("audio/"+gcs_fileName)
    blob.delete()
    print(gcs_fileName+"deleted.") 
    
    

@csrf_exempt
def summaryToSpring(request):
    try:
        transcript = request.POST.get('transcript')
        print("")
        summary = summarize_transcript(transcript)
        
        
    except Exception as e:
        print(str(e))
        return HttpResponse(f"error :{e}")
    
    return JsonResponse({"summary": summary})
        
        
        
def summarize_transcript(transcript):
    text = transcript
    text = text.replace('\n', ' ')

    tokenizer = PreTrainedTokenizerFast.from_pretrained('digit82/kobart-summarization')
    model = BartForConditionalGeneration.from_pretrained('digit82/kobart-summarization')

    text = text.replace('\n', ' ')

    result = ""
    max_len = len(text)
    print(max_len)

    if(len(text)>=1000):
        print("long sentence")
        kkma = Kkma()
        sentences = kkma.sentences(text)
        
        sentence = [""]
        s_index = 0
        for sen in sentences:
            
            if(len(sentence[s_index])<1000):

                sentence[s_index] += sen
            else:
                new_start = sentence[s_index][-len_sen:]
                sentence[s_index] = sentence[s_index][:-len_sen]
                s_index += 1
                sentence.append(new_start)
                
            len_sen = len(sen)

        if len(sentence[-1])<=150:
            last_sentence = sentence.pop(-1)
            sentence[-1] += last_sentence
        
        for s in sentence:
            
            len_s = len(s)
            
            # if(len_s<)
            raw_input_ids = tokenizer.encode(s)
            input_ids = [tokenizer.bos_token_id] + raw_input_ids + [tokenizer.eos_token_id]
            summary_ids = model.generate(torch.tensor([input_ids]),  num_beams=1,  max_length=len_s,  eos_token_id=1)
            re = tokenizer.decode(summary_ids.squeeze().tolist(), skip_special_tokens=True)
            result += " "
            
            if len(re)<(len_s):
                result += re

            
    elif(max_len<=150):
            result = "요약하기에는 너무 짧습니다."


    else:
        raw_input_ids = tokenizer.encode(text)
        input_ids = [tokenizer.bos_token_id] + raw_input_ids + [tokenizer.eos_token_id]
        
        summary_ids = model.generate(torch.tensor([input_ids]),  num_beams=1,  max_length=max_len,  eos_token_id=1)
        result = tokenizer.decode(summary_ids.squeeze().tolist(), skip_special_tokens=True)
        
        if len(result)>max_len:
            result = "요약하기에는 길이, 내용이 부적절합니다."
                 
    return result


    
def split_flac(input_flac, output_dir, chunk_duration_sec):
    print("split_flac")
    os.makedirs(output_dir, exist_ok=True)

    input_basename = os.path.basename(input_flac)
    output_prefix = output_dir + '/' + os.path.splitext(input_basename)[0]

    # 청크 크기 (초)
    chunk_size = int(chunk_duration_sec * 1000)

    audio_paths=[]
    # 청크로 음성 파일을 분할
    audio = AudioSegment.from_file(input_flac, format="flac")
    for i, chunk in enumerate(audio[::chunk_size]):
        output_file = f"{output_prefix}_{i:03d}.flac"
        chunk.export(output_file, format="flac")    
        audio_paths.append(output_file)
    
    return audio_paths


    
def transcribe_audio_part(client,audio_path):

    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=44100,
        language_code="ko-KR",
        enable_word_time_offsets=True,
        audio_channel_count=2,
    )

    response = client.recognize(config=config, audio=audio)
    
    transcript = ""
    words = []
    
    for result in response.results:
        transcript = result.alternatives[0].transcript
        words = result.alternatives[0].words
    
    tandw = []
        
    for w in words:
        word = {}
        word['word'] = w.word
        word['start'] = w.start_time.seconds
        tandw.append(word)
    
    return {"audio_path": audio_path, "transcript": transcript, "words":tandw}      
        
        

def transcribe_audio_parallel(audio_paths):

    client = speech.SpeechClient()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(transcribe_audio_part, client, audio_path) for audio_path in audio_paths]
        
        results = []
        # 모든 작업이 완료될 때까지 기다립니다.
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error: {e}")  

        sorted_results = sorted(results,key=lambda x: x["audio_path"])

        transcript = ""
        wandt = []
        
        for index,result in enumerate(sorted_results):
            timeCompensation = index*30
            for w in result['words']:
                w['start'] += timeCompensation
            
            transcript += " "
            transcript += result['transcript']
            wandt += result['words']
            
        topWords = get_top_words(transcript)    

    return {"transcript":transcript, "words":wandt, "topWords":topWords}
    



    
    
    
    
    
    
    
    