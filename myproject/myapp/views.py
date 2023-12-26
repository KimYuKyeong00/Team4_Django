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
from collections import Counter
import torch
from transformers import PreTrainedTokenizerFast
from transformers import BartForConditionalGeneration
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
        
        print(folder_dir)
        print(fileName)
        
        flac_dir = videoToAudio(folder_dir,fileName)
        gcs_fileName = makeFileName('flac')
        bn =upload_file_to_gcs(flac_dir,gcs_fileName)
        flacInGCS = "gs://audio_storage_tpj/"+bn
        result = transcribe_audio(flacInGCS)
        deleteUsedLocalFile(flac_dir)
        deleteUsedGCSFile(gcs_fileName)
        
    except Exception as e:
        print(str(e))
        return HttpResponse(f"error :{e}")
    
    return HttpResponse(result,content_type='application/json')

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
    response = operation.result(timeout=600)
    
    response_json = MessageToJson(response._pb)
    jo = json.loads(response_json)
    
    transcript = ""
    words = []
    
    for j in jo.get("results"):
        transcript += j.get("alternatives")[0].get("transcript")
        words += j.get("alternatives")[0].get("words")
        
    top_words = get_top_words(transcript)
    
    results={
        "transcript":transcript,
        "words":words,
        "top_words":top_words,
    }
    
    final_response = json.dumps(results)
    
    return final_response


def get_top_words(transcript):
    okt = Okt()
    stop_word = "\n\n 아 휴 아이구 아이쿠 아이고 은 는 이 가 어 나 우리 저희 따라 그냥 이제 의해 을 를 에 의 가 으로 로 에게 뿐이다 의거하여 근거하여 입각하여 기준으로 예하면 예를 들면 예를 들자면 저 소인 소생 저희 지말고 하지마 하지마라 다른 물론 또한 그리고 비길수 없다 해서는 안된다 뿐만 아니라 만이 아니다 만은 아니다 막론하고 관계없이 그치지 않다 그러나 그런데 하지만 든간에 논하지 않다 따지지 않다 설사 비록 더라도 아니면 만 못하다 하는 편이 낫다 불문하고 향하여 향해서 향하다 쪽으로 틈타 이용하여 타다 오르다 제외하고 이 외에 이 밖에 하여야 비로소 한다면 몰라도 외에도 이곳 여기 부터 기점으로 따라서 할 생각이다 하려고하다 이리하여 그리하여 그렇게 함으로써 하지만 일때 할때 앞에서 중에서 보는데서 으로써 로써 까지 해야한다 일것이다 반드시 할줄알다 할수있다 할수있어 임에 틀림없다 한다면 등 등등 제 겨우 단지 다만 할뿐 딩동 댕그 대해서 대하여 대하면 훨씬 얼마나 얼마만큼 얼마큼 남짓 여 얼마간 약간 다소 좀 조금 다수 몇 얼마 지만 하물며 또한 그러나 그렇지만 하지만 이외에도 대해 말하자면 뿐이다 다음에 반대로 반대로 말하자면 이와 반대로 바꾸어서 말하면 바꾸어서 한다면 만약 그렇지않으면 까악 툭 딱 삐걱거리다 보드득 비걱거리다 꽈당 응당 해야한다 에 가서 각 각각 여러분 각종 각자 제각기 하도록하다 와 과 그러므로 그래서 고로 한 까닭에 하기 때문에 거니와 이지만 대하여 관하여 관한 과연 실로 아니나다를가 생각한대로 진짜로 한적이있다 하곤하였다 하 하하 허허 아하 거바 와 오 왜 어째서 무엇때문에 어찌 하겠는가 무슨 어디 어느곳 더군다나 하물며 더욱이는 어느때 언제 야 이봐 어이 여보시오 흐흐 흥 휴 헉헉 헐떡헐떡 영차 여차 어기여차 끙끙 아야 앗 아야 콸콸 졸졸 좍좍 뚝뚝 주룩주룩 솨 우르르 그래도 또 그리고 바꾸어말하면 바꾸어말하자면 혹은 혹시 답다 및 그에 따르는 때가 되어 즉 지든지 설령 가령 하더라도 할지라도 일지라도 지든지 몇 거의 하마터면 인젠 이젠 된바에야 된이상 만큼 어찌됏든 그위에 게다가 점에서 보아 비추어 보아 고려하면 하게될것이다 일것이다 비교적 좀 보다더 비하면 시키다 하게하다 할만하다 의해서 연이서 이어서 잇따라 뒤따라 뒤이어 결국 의지하여 기대여 통하여 자마자 더욱더 불구하고 얼마든지 마음대로 주저하지 않고 곧 즉시 바로 당장 하자마자 밖에 안된다 하면된다 그래 그렇지 요컨대 다시 말하자면 바꿔 말하면 즉 구체적으로 말하자면 시작하여 시초에 이상 허 헉 허걱 바와같이 해도좋다 해도된다 게다가 더구나 하물며 와르르 팍 퍽 펄렁 동안 이래 하고있었다 이었다 에서 로부터 까지 예하면 했어요 해요 함께 같이 더불어 마저 마저도 양자 모두 습니다 가까스로 하려고하다 즈음하여 다른 다른 방면으로 해봐요 습니까 했어요 말할것도 없고 무릎쓰고 개의치않고 하는것만 못하다 하는것이 낫다 매 매번 들 모 어느것 어느 로써 갖고말하자면 어디 어느쪽 어느것 어느해 어느 년도 라 해도 언젠가 어떤것 어느것 저기 저쪽 저것 그때 그럼 그러면 요만한걸 그래 그때 저것만큼 그저 이르기까지 할 줄 안다 할 힘이 있다 너 너희 당신 어찌 설마 차라리 할지언정 할지라도 할망정 할지언정 구토하다 게우다 토하다 메쓰겁다 옆사람 퉤 쳇 의거하여 근거하여 의해 따라 힘입어 그 다음 버금 두번째로 기타 첫번째로 나머지는 그중에서 견지에서 형식으로 쓰여 입장에서 위해서 단지 의해되다 하도록시키다 뿐만아니라 반대로 전후 전자 앞의것 잠시 잠깐 하면서 그렇지만 다음에 그러한즉 그런즉 남들 아무거나 어찌하든지 같다 비슷하다 예컨대 이럴정도로 어떻게 만약 만일 위에서 서술한바와같이 인 듯하다 하지 않는다면 만약에 무엇 무슨 어느 어떤 아래윗 조차 한데 그럼에도 불구하고 여전히 심지어 까지도 조차도 하지 않도록 않기 위하여 때 시각 무렵 시간 동안 어때 어떠한 하여금 네 예 우선 누구 누가 알겠는가 아무도 줄은모른다 줄은 몰랏다 하는 김에 겸사겸사 하는바 그런 까닭에 한 이유는 그러니 그러니까 때문에 그 너희 그들 너희들 타인 것 것들 너 위하여 공동으로 동시에 하기 위하여 어찌하여 무엇때문에 붕붕 윙윙 나 우리 엉엉 휘익 윙윙 오호 아하 어쨋든 만 못하다 하기보다는 차라리 하는 편이 낫다 흐흐 놀라다 상대적으로 말하자면 마치 아니라면 쉿 그렇지 않으면 그렇지 않다면 안 그러면 아니었다면 하든지 아니면 이라면 좋아 알았어 하는것도 그만이다 어쩔수 없다 하나 일 일반적으로 일단 한켠으로는 오자마자 이렇게되면 이와같다면 전부 한마디 한항목 근거로 하기에 아울러 하지 않도록 않기 위해서 이르기까지 이 되다 로 인하여 까닭으로 이유만으로 이로 인하여 그래서 이 때문에 그러므로 그런 까닭에 알 수 있다 결론을 낼 수 있다 으로 인하여 있다 어떤것 관계가 있다 관련이 있다 연관되다 어떤것들 에 대해 이리하여 그리하여 여부 하기보다는 하느니 하면 할수록 운운 이러이러하다 하구나 하도다 다시말하면 다음으로 에 있다 에 달려 있다 우리 우리들 오히려 하기는한데 어떻게 어떻해 어찌됏어 어때 어째서 본대로 자 이 이쪽 여기 이것 이번 이렇게말하자면 이런 이러한 이와 같은 요만큼 요만한 것 얼마 안 되는 것 이만큼 이 정도의 이렇게 많은 것 이와 같다 이때 이렇구나 것과 같이 끼익 삐걱 따위 와 같은 사람들 부류의 사람들 왜냐하면 중의하나 오직 오로지 에 한하다 하기만 하면 도착하다 까지 미치다 도달하다 정도에 이르다 할 지경이다 결과에 이르다 관해서는 여러분 하고 있다 한 후 혼자 자기 자기집 자신 우에 종합한것과같이 총적으로 보면 총적으로 말하면 총적으로 대로 하다 으로서 참 그만이다 할 따름이다 쿵 탕탕 쾅쾅 둥둥 봐 봐라 아이야 아니 와아 응 아이 참나 년 월 일 령 영 일 이 삼 사 오 육 륙 칠 팔 구 이천육 이천칠 이천팔 이천구 하나 둘 셋 넷 다섯 여섯 일곱 여덟 아홉 령 영 이 있 하 것 들 그 되 수 이 보 않 없 나 사람 주 아니 등 같 우리 때 년 가 한 지 대하 오 말 일 그렇 위하 때문 그것 두 말하 알 그러나 받 못하 일 그런 또 문제 더 사회 많 그리고 좋 크 따르 중 나오 가지 씨 시키 만들 지금 생각하 그러 속 하나 집 살 모르 적 월 데 자신 안 어떤 내 내 경우 명 생각 시간 그녀 다시 이런 ㅋ 은 앞 보이 번 나 다른 어떻 여자 개 전 들 사실 이렇 점 싶 말 정도 좀 원 잘 통하 놓"
    sw = set(stop_word.split(" "))
    sentence = okt.morphs(transcript)
    sentence = [w for w in sentence if w not in sw]
    top_words = Counter(sentence).most_common(3)

    return top_words


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
    


def summaryToSpring(request):
    try:
        transcript = request.GET.get('transcript')
        print("")
        summary = summarize_transcript(transcript)
        
        
    except Exception as e:
        print(str(e))
        return HttpResponse(f"error :{e}")
    
    return HttpResponse(summary)
        
        
def summarize_transcript(transcript):
    text = transcript
    
    tokenizer = PreTrainedTokenizerFast.from_pretrained('digit82/kobart-summarization')
    model = BartForConditionalGeneration.from_pretrained('digit82/kobart-summarization')

    raw_input_ids = tokenizer.encode(text)
    input_ids = [tokenizer.bos_token_id] + raw_input_ids + [tokenizer.eos_token_id]

    summary_ids = model.generate(torch.tensor([input_ids]),  num_beams=4,  max_length=512,  eos_token_id=1)
    result = tokenizer.decode(summary_ids.squeeze().tolist(), skip_special_tokens=True)
 
    return result
    
    
    
    
    
    
    
    
    