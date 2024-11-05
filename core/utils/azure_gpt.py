import json
import os
import aiohttp
from datetime import datetime
from typing import Dict, Optional
from config.azure_config import GPT4V_ENDPOINT, HEADERS, MODEL_CONFIG

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)  # Ensure log directory exists

class AzureGPTClient:
    @staticmethod
    async def generate_response(system_prompt: str, user_prompt: str, 
                            temperature: Optional[float] = None) -> Optional[str]:
        """GPT 응답 생성 및 로깅"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature or MODEL_CONFIG["temperature"],
                    "top_p": MODEL_CONFIG["top_p"],
                    "max_tokens": MODEL_CONFIG["max_tokens"]
                }
                
                # 타임아웃 설정 추가
                timeout = aiohttp.ClientTimeout(total=60)  # 60초 타임아웃
                
                async with session.post(
                    GPT4V_ENDPOINT,
                    headers=HEADERS,
                    json=payload,
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # 응답 구조 로깅
                        print("API Response structure:", result)
                        
                        # 응답에서 텍스트 추출
                        if "choices" in result and len(result["choices"]) > 0:
                            response_text = result["choices"][0]["message"]["content"]
                            return response_text
                        else:
                            print("Unexpected response structure:", result)
                            return None
                    else:
                        error_text = await response.text()
                        print(f"Error status {response.status}: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            print("Request timed out after 60 seconds")
            return None
        except Exception as e:
            print(f"Error in generate_response: {str(e)}")
            return None

    @staticmethod
    async def generate_structured_response(system_prompt: str, 
                                        user_prompt: str, 
                                        output_format: Dict,
                                        temperature: Optional[float] = None) -> Optional[Dict]:
        """구조화된 형식으로 GPT 응답 생성 및 로깅"""
        format_instruction = f"\n출력 형식은 다음과 같아야 합니다:\n{json.dumps(output_format, ensure_ascii=False)}"
        full_prompt = user_prompt + format_instruction

        response = await AzureGPTClient.generate_response(
            system_prompt, 
            full_prompt, 
            temperature
        )
        
        if response:
            try:
                response_data = json.loads(response)  # Attempt to parse JSON
                await AzureGPTClient.log_response(full_prompt, response)  # Log structured response
                return response_data
            except json.JSONDecodeError as e:
                print(f"Error parsing response: {e}")
                await AzureGPTClient.log_response(full_prompt, response, error=True)  # Log if JSON parsing fails
                return None
        
        return None

    @staticmethod
    async def log_response(prompt: str, response: str, error: bool = False) -> None:
        """Log GPT responses to a file for debugging"""
        log_type = "error" if error else "response"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{LOG_DIR}/{log_type}_log_{timestamp}.txt"
        
        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write("Prompt:\n" + prompt + "\n\n")
            log_file.write("Response:\n" + response + "\n")

        print(f"{log_type.capitalize()} logged to {log_filename}")

    @staticmethod
    def parse_json_response(response_text: str) -> Optional[Dict]:
        """GPT 응답을 JSON으로 파싱"""
        try:
            # 응답에서 JSON 부분만 추출
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            return None
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            return None

    @staticmethod
    async def generate_structured_response(system_prompt: str, 
                                    user_prompt: str, 
                                    output_format: Dict,
                                    temperature: Optional[float] = None) -> Optional[Dict]:
        """구조화된 형식으로 GPT 응답 생성"""
        format_instruction = f"\n출력 형식은 다음과 같아야 합니다:\n{json.dumps(output_format, ensure_ascii=False)}"
        full_prompt = user_prompt + format_instruction
        
        response = await AzureGPTClient.generate_response(
            system_prompt, 
            full_prompt, 
            temperature
        )
        
        if response:
            parsed_response = AzureGPTClient.parse_json_response(response)
            if parsed_response:
                return parsed_response
                
        return None