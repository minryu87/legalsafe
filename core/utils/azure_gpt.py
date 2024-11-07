import json
import os
import aiohttp
from datetime import datetime
from typing import Dict, Optional

from config.azure_config import GPT4V_ENDPOINT, HEADERS, MODEL_CONFIG

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)  # Ensure log directory exists

class AzureGPTClient:
    async def generate_response(self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> Optional[str]:
        """GPT 응답 생성"""
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
                
                timeout = aiohttp.ClientTimeout(total=60)
                
                async with session.post(
                    GPT4V_ENDPOINT,
                    headers=HEADERS,
                    json=payload,
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("API Response structure:", result)
                        
                        if "choices" in result and len(result["choices"]) > 0:
                            response_text = result["choices"][0]["message"]["content"]
                            return response_text

                    error_text = await response.text()
                    print(f"Error status {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"Error in generate_response: {str(e)}")
            return None

    async def generate_structured_response(self,
        system_prompt: str, 
        user_prompt: str, 
        output_format: Dict,
        temperature: Optional[float] = None
    ) -> Optional[Dict]:
        """구조화된 형식으로 GPT 응답 생성"""
        try:
            format_instruction = (
                f"\n출력 형식은 다음과 같아야 합니다:\n"
                f"{json.dumps(output_format, ensure_ascii=False, indent=2)}\n"
                f"위 형식을 정확히 따라주시고, 모든 키를 반드시 포함해 주세요."
            )
            full_prompt = user_prompt + format_instruction

            response = await self.generate_response(
                system_prompt=system_prompt, 
                user_prompt=full_prompt, 
                temperature=temperature
            )

            if not response:
                return None

            # JSON 파싱 시도
            try:
                # 코드 블록 제거
                if '```json' in response:
                    start_idx = response.find('```json') + 7
                    end_idx = response.rfind('```')
                    response = response[start_idx:end_idx].strip()
                elif '```' in response:
                    start_idx = response.find('```') + 3
                    end_idx = response.rfind('```')
                    response = response[start_idx:end_idx].strip()

                # JSON 부분 추출
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end].strip()
                    result = json.loads(json_str)

                    # 출력 형식 검증
                    if all(key in result for key in output_format.keys()):
                        print(f"Successfully parsed result: {result}")  # 디버깅용
                        return result

                print(f"Invalid format in response: {response}")  # 디버깅용
                return None

            except json.JSONDecodeError as e:
                print(f"JSON parse error: {str(e)}\nResponse: {response}")
                return None
            except Exception as e:
                print(f"Error processing response: {str(e)}")
                return None

        except Exception as e:
            print(f"Error in generate_structured_response: {str(e)}")
            return None

    async def log_response(self, prompt: str, response: str, error: bool = False) -> None:
        """Log GPT responses to a file for debugging"""
        log_type = "error" if error else "response"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{LOG_DIR}/{log_type}_log_{timestamp}.txt"
        
        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write("Prompt:\n" + prompt + "\n\n")
            log_file.write("Response:\n" + response + "\n")

        print(f"{log_type.capitalize()} logged to {log_filename}")

    def parse_json_response(self, response_text: str) -> Optional[Dict]:
        """GPT 응답을 JSON으로 파싱"""
        try:
            # 코드 블록 제거
            if '```json' in response_text:
                start_idx = response_text.find('```json') + 7
                end_idx = response_text.rfind('```')
                response_text = response_text[start_idx:end_idx].strip()
            elif '```' in response_text:
                start_idx = response_text.find('```') + 3
                end_idx = response_text.rfind('```')
                response_text = response_text[start_idx:end_idx].strip()
            
            # JSON 부분만 추출 시도
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end].strip()
                print(f"Parsed JSON string: {json_str}")  # 디버깅용 로그
                return json.loads(json_str)
                
            print(f"No JSON found in response: {response_text}")  # 디버깅용 로그
            return None
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}\nResponse text: {response_text}")
            return None
        except Exception as e:
            print(f"Unexpected error parsing response: {e}")
            return None
