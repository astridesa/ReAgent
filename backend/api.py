from openai import OpenAI,AzureOpenAI
import json
import os
import time
from dotenv import load_dotenv
import os
import logging

from difflib import SequenceMatcher

def is_similar(a, b, threshold=0.8):
    # 计算两个字符串的相似度
    return SequenceMatcher(None, a, b).ratio() >= threshold

def remove_similar_prefix(text, prefix, threshold=0.8):
    # 检查文本开头是否与前缀相似
    if is_similar(text[:len(prefix)], prefix, threshold):
        return text[len(prefix):].strip()
    return text



# logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import yaml

def load_env():
    with open("config/env.yaml", "r")  as f:
        service = yaml.safe_load(f)['services']
    return service

 
global services
services = load_env()
# print(services)

def api_call(messages, model="deepseek", temperature=1.0, max_tokens=4096, max_retries=10, json_format=False, stream=False):
    if "gpt" in model or "o1" in model:
        api_key = services['openai']['api_key']
        base_url = services['openai']['base_url']
    elif "qwen" in model:
        api_key = services['qwen']['api_key']
        base_url = services['qwen']['base_url']
    elif "deepseek" in model:
        api_key = services['deepseek']['api_key']
        base_url = f"{services['deepseek']['base_url']}"
    elif "claude" in model:
        api_key = services['claude']['api_key']
        base_url = services['claude']['base_url']  

 
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
 
    )

    for _ in range(max_retries):
        try:
            if not json_format:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=stream,  # 启用流式输出,
                   
                )
                if not response.choices[0].message.content:
                    continue
                return response.choices[0].message.content
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    stream=stream  # 启用流式输出
                )
                if not response.choices[0].message.content:
                    continue
                json_response = eval(response.choices[0].message.content)

                return json_response
        except Exception as e:
            logger.error(f"Error while calling API: {str(e)}")
            time.sleep(2**(_+1))
            continue
    raise Exception("Max retries reached. API call failed.")

def api_call_completion(messages, model="deepseek-chat", stop_list = None):
    if "gpt" in model or "o1" in model:
        api_key = services['openai']['api_key']
        base_url = services['openai']['base_url']
    elif "qwen" in model:
        api_key = services['qwen']['api_key']
        base_url = services['qwen']['base_url']
    elif "deepseek" in model:
        api_key = services['deepseek']['api_key']
        base_url = f"{services['deepseek']['base_url']}"
    elif "claude" in model:
        api_key = services['claude']['api_key']
        base_url = services['claude']['base_url']  

    client = OpenAI(
        base_url= base_url,
        api_key= api_key
    )
 

    for r in range(10):
        try:
            prefix = stop_list[0]
            prefix = f"Step {int(prefix[5]) - 1}:"
            response = client.chat.completions.create(
                model= model,
                messages= messages,
                stop= stop_list,
                stream= False,
                max_tokens= 4096,
                temperature= 0.0, 
                # extra_body={"prefix": prefix},
                # timeout= 300,
                # extra_body={'repetition_penalty': 2},
            )
            current_text = response.choices[0].message.content
            if current_text:
                return current_text
            else:
                print("返回为空。")
                continue
 
        except Exception as e:
            print(e)
            time.sleep(2**(r+1))

    raise "Error api call"
  
 
if __name__ == "__main__":
    # Example usage
    messages = [
    {
        "role": "user",
        "content": "https://en.wikipedia.org/wiki/IEEE_Frank_Rosenblatt_Award"
    }]
    print(api_call(messages, "deepseek-chat"))
 
#  claude-3-5-sonnet-20241022