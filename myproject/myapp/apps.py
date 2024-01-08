from django.apps import AppConfig
import torch
from transformers import BartForConditionalGeneration, BartConfig

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    
    @classmethod
    def ready(cls):
        if hasattr(cls, 'tuned_model'):
            return
        
        
        # # 여기를 학습된 모델이 있는 경로로 설정
        # global model_dir
        # model_dir = "D:/finetunedModel/tuned_model.bin"
        
        
        # state_dict = torch.load(model_dir, map_location=torch.device("cpu"))
        # config = BartConfig.from_json_file("D:/finetunedModel/config.json")
        
        # global tuned_model
        # tuned_model = BartForConditionalGeneration(config)
        # tuned_model.load_state_dict(state_dict, strict=False)
        # tuned_model.eval()
    
        
        
    
