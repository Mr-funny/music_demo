import requests
import json
import base64
import os
import mimetypes
import logging
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# 配置日志处理器使用 utf-8 编码
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 标准输出使用 stdout
        logging.FileHandler('app.log', encoding='utf-8')  # 文件输出使用 utf-8 编码
    ]
)

# 创建 Flask 应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'downloads'

class MusicGenerator:
    def __init__(self, api_key):
        """
        初始化音乐生成器
        :param api_key: API密钥
        """
        self.api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJKSyIsIlVzZXJOYW1lIjoiSksiLCJBY2NvdW50IjoiIiwiU3ViamVjdElEIjoiMTg2MjA3MDMyNzczNjAyNTEwMCIsIlBob25lIjoiMTMxMTY3OTM3MjUiLCJHcm91cElEIjoiMTg2MjA3MDMyNzczMTgzMDc5NiIsIlBhZ2VOYW1lIjoiIiwiTWFpbCI6IiIsIkNyZWF0ZVRpbWUiOiIyMDI0LTEyLTEwIDExOjI1OjI1IiwiVG9rZW5UeXBlIjoxLCJpc3MiOiJtaW5pbWF4In0.Xheo0uYyQT_RezMZIncWqHKWhjJMP3nBoMgrW_A7gVCCvMUfsG0fExsjjGeAowt6AqVKaHLNLlTwB6nKEXBoYqymwdDBLa57Amd8vPLnYRBw1ql4pv3pVUkPAhAIACSkLS4Oqziz9XEFiLUARt6gR5kWknuzctSKVNsYZHnN0Yky5dwuNTXNr7Mpfcx9yc7Wk-VRvdSACsdBNw5FrCiJYzSN5nFddUUCv-HNxqgPN8fpfV2fgjSLpCy_hjvUF_woVm8MqXtAz-GVtJVOYLp84YJBscZo7qQSWyYDFsavRfyBkdXQQJTLq0Yoohr_WHgjBxBd-6PRrjOze4zSPap71g"
        self.upload_url = "https://api.minimax.chat/v1/music_upload"
        self.generation_url = "https://api.minimax.chat/v1/music_generation"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logging.info("MusicGenerator initialized")

    def upload_file(self, file_path, timeout=60, max_retries=3):
        """
        上传音频文件
        :param file_path: 音频文件路径
        :param timeout: 请求超时时间（秒）
        :param max_retries: 最大重试次数
        :return: 上传后的文件ID
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                if not os.path.exists(file_path):
                    logging.error(f"文件不存在: {file_path}")
                    return None

                # 获取文件的MIME类型
                mime_type = mimetypes.guess_type(file_path)[0] or 'audio/mpeg'
                
                # 构建multipart/form-data请求
                payload = {
                    'purpose': 'song'  # 设置purpose为song
                }
                
                files = [
                    ('file', (
                        os.path.basename(file_path), 
                        open(file_path, 'rb'), 
                        mime_type
                    ))
                ]
                
                logging.info(f"开始上传文件（第{retry_count + 1}次尝试）: {os.path.basename(file_path)}")
                
                response = requests.post(
                    self.upload_url,
                    headers={
                        'Authorization': f"Bearer {self.api_key}"
                    },
                    data=payload,
                    files=files,
                    timeout=timeout  # 增加超时时间
                )
                
                response.raise_for_status()
                result = response.json()
                logging.info(f"上传响应数据: {json.dumps(result, indent=2)}")
                
                if result.get('base_resp', {}).get('status_code') == 0:
                    return result
                else:
                    logging.error(f"上传失败响应: {result}")
                    return None
                
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count < max_retries:
                    logging.warning(f"上传超时，正在进行第{retry_count + 1}次重试...")
                    continue
                else:
                    logging.error("上传多次超时，放弃重试")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"上传请求失败: {str(e)}")
                return None
            except Exception as e:
                logging.error(f"上传文件时发生错误: {str(e)}")
                return None
            finally:
                # 确保文件被关闭
                if 'files' in locals() and files[0][1][1]:
                    files[0][1][1].close()

    def separate_audio(self, file_path):
        """
        分离音频文件为人声和伴奏
        :param file_path: 音频文件路径
        :return: (voice_id, instrumental_id) 元组
        """
        try:
            logging.info(f"开始分离音频: {os.path.basename(file_path)}")
            
            # 上传原始文件
            file_id = self.upload_file(file_path)
            if not file_id:
                return None, None
            
            # 调用分离API
            separate_url = f"{self.upload_url}/separate"
            payload = {"file_id": file_id}
            
            response = requests.post(
                separate_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("status") == "success":
                voice_id = result.get("voice_id")
                instrumental_id = result.get("instrumental_id")
                logging.info(f"音频分离成功 - 人声ID: {voice_id}, 伴奏ID: {instrumental_id}")
                return voice_id, instrumental_id
            else:
                raise Exception(f"分离失败: {result.get('message')}")
                
        except Exception as e:
            logging.error(f"分离音频时发生错误: {str(e)}")
            return None, None

    def generate_music(self, prompt=None, style="classical", duration=30, voice_path=None, instrumental_path=None, lyrics=None):
        try:
            logging.info("=== 开始生成音乐 ===")
            logging.info(f"音频文件路径: {voice_path}")
            logging.info(f"歌词内容: {lyrics}")
            
            voice_id = None  # 初始化变量
            instrumental_id = None  # 初始化变量
            
            if voice_path:
                logging.info("开始上传音频文件...")
                upload_response = self.upload_file(voice_path)
                logging.info(f"上传响应: {json.dumps(upload_response, indent=2)}")
                
                if isinstance(upload_response, dict):
                    voice_id = upload_response.get('voice_id', '')
                    instrumental_id = upload_response.get('instrumental_id', '')
                    logging.info(f"上传成功 - voice_id: {voice_id}, instrumental_id: {instrumental_id}")
                else:
                    logging.error("上传失败，无法获取音频ID")
                    return None

            # 在歌词前后添加 ##
            if lyrics:
                lyrics = f"##\n{lyrics}\n##"

            # 构建请求参数
            payload = {
                'refer_voice': voice_id if voice_id else "",
                'refer_instrumental': instrumental_id if instrumental_id else "",
                'lyrics': lyrics if lyrics else "",
                'model': 'music-01',
                'audio_setting': '{"sample_rate":44100,"bitrate":256000,"format":"mp3"}'
            }
            
            try:
                logging.info("开始生成音乐...")
                logging.info(f"生成请求数据: {json.dumps(payload, indent=2)}")
                
                response = requests.post(
                    self.generation_url,
                    headers={
                        'Authorization': f"Bearer {self.api_key}",
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    data=payload,
                    timeout=60
                )
                
                logging.info(f"响应状态码: {response.status_code}")
                logging.info(f"响应内容: {response.text}")
                
                if response.status_code == 200:
                    try:
                        # 尝试解析响应内容
                        response_text = response.text.strip()  # 移除可能的空白字符
                        if response_text:
                            result = json.loads(response_text)
                            if result and result.get("data") and result["data"].get("audio"):
                                # 使用 app.config['UPLOAD_FOLDER'] 作为保存目录
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                output_file = os.path.join(app.config['UPLOAD_FOLDER'], f'generated_music_{timestamp}.mp3')
                                
                                # 确保目录存在
                                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                                
                                # 解码音频数据
                                audio_data = bytes.fromhex(result["data"]["audio"])
                                with open(output_file, "wb") as f:
                                    f.write(audio_data)
                                
                                logging.info(f"音乐生成成功，保存为: {output_file}")
                                return output_file
                            else:
                                error_msg = result.get('base_resp', {}).get('status_msg', '未知错误')
                                raise Exception(f"生成失败: {error_msg}")
                        else:
                            raise Exception("响应内容为空")
                    except json.JSONDecodeError as e:
                        logging.error(f"JSON解析错误: {str(e)}")
                        logging.error(f"原始响应内容: {response.text}")
                        raise Exception("响应格式错误")
                else:
                    raise Exception(f"请求失败: HTTP {response.status_code}")
                
            except Exception as e:
                logging.error(f"生成音乐时发生错误: {str(e)}")
                return None

        except Exception as e:
            logging.error("=== 生成音乐时发生错误 ===")
            logging.error(f"错误类型: {type(e)}")
            logging.error(f"错误信息: {str(e)}")
            logging.error("详细堆栈:", exc_info=True)
            return None

    async def download_suno_audio(self, suno_url, output_dir='downloads'):
        """异步下载 Suno 音频文件"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            logging.info("开始下载Suno音频: %s", suno_url)
            
            # 从URL中提取音频ID
            song_id = suno_url.split('/')[-1]
            # 构建实际的音频URL
            audio_url = f"https://cdn1.suno.ai/{song_id}.mp3"
            
            # 更新请求头，模拟真实浏览器请求
            headers = {
                'Accept-Encoding': 'identity;q=1, *;q=0',
                'Referer': 'https://suno.com/',
                'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, headers=headers) as response:
                    if response.status == 200:
                        output_file = os.path.join(output_dir, f'suno_{song_id}.mp3')
                        with open(output_file, 'wb') as f:
                            while True:
                                chunk = await response.content.read(8192)
                                if not chunk:
                                    break
                                f.write(chunk)
                        logging.info("Suno音频下载成功: %s", output_file)
                        return output_file
                    else:
                        logging.error("下载失败，状态码: %d", response.status)
                        return None
                    
        except Exception as e:
            logging.error("下载Suno音频时发生错误: %s", str(e))
            return None

    def generate_from_suno(self, suno_url, prompt=None, style="classical", duration=30):
        try:
            # 使用同步方式下载
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            downloaded_file = loop.run_until_complete(self.download_suno_audio(suno_url))
            loop.close()
            
            if not downloaded_file:
                logging.error("Suno音频下载失败")
                return None
            
            logging.info(f"Suno音频下载成功: {downloaded_file}")
            
            # 2. 使用下载的音频生成新的音频
            output_file = self.generate_music(
                prompt=prompt or "基于上传的音频创作一段优美的音乐，保持原曲风格",
                style=style,
                duration=duration,
                voice_path=downloaded_file
            )
            
            if output_file:
                logging.info(f"基于Suno音频生成新音频成功: {output_file}")
            else:
                logging.error("基于Suno音频生成新音频失败")
            
            return output_file
            
        except Exception as e:
            logging.error(f"从Suno音频生成新音频时发生错误: {str(e)}")
            return None

class LyricsPolisher:
    def __init__(self, api_key, group_id):
        self.api_key = api_key
        self.group_id = group_id
        self.url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "mm-group-id": self.group_id
        }
        logging.info("LyricsPolisher initialized")
    
    async def polish_lyrics(self, original_lyrics):
        """使用 Minimax API 异步润色歌词"""
        try:
            logging.info("开始润色歌词: %s", repr(original_lyrics))
            
            # 构建更清晰的 system prompt
            system_prompt = """你是一个专业的语义节奏大师。你的任务是：
1. 分析输入歌词的语义
2. 仅通过添加换行符来添加节奏和停顿：
   - 使用双换行符"\n"表示短停顿
   - 使用双换行符"\n\n"表示长停顿
3. 不要修改任何原始歌词内容
4. 不要添加任何其他标点或符号
5. 不要添加任何额外说明或注释"""

            payload = {
                "model": "abab5.5-chat",
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": original_lyrics
                    }
                ],
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000,  # 增加 token 限制以适应更长的歌词
                "echo": False 
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=self.headers, json=payload) as response:
                    response_text = await response.text()
                    logging.info("API 响应内容: %s", response_text)
                    
                    if response.status != 200:
                        logging.error("API 请求失败，状态码: %d", response.status)
                        return None
                    
                    result = json.loads(response_text)
                    
                    # 检查响应状态
                    if result.get("base_resp", {}).get("status_code") != 0:
                        error_msg = result.get("base_resp", {}).get("status_msg", "未知错误")
                        logging.error("API 返回错误: %s", error_msg)
                        return None
                    
                    # 获取润色后的歌词
                    if "choices" in result and len(result["choices"]) > 0:
                        # 获取润色后的歌词并去除首尾空白字符
                        polished_lyrics = result["choices"][0]["message"]["content"].strip()
                        
                        # 直接在歌词前后添加##，不添加任何换行符
                        final_lyrics = f"##" + polished_lyrics + "##"
                        
                        # 记录处理结果
                        logging.info("润色后的歌词 (原始格式):\n%s", repr(final_lyrics))
                        logging.info("润色后的歌词 (显示格式):\n%s", final_lyrics)
                        
                        return final_lyrics
                    else:
                        logging.error("响应中没有找到歌词内容")
                        return None
            
        except Exception as e:
            logging.error("歌词润色过程中发生错误: %s", str(e))
            return None

# 添加路由处理
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/generate', methods=['POST'])
async def generate():
    try:
        logging.info("收到生成请求")
        data = request.json
        logging.info(f"请求数据: {json.dumps(data, ensure_ascii=False)}")
        
        suno_url = data.get('suno_url')
        original_lyrics = data.get('lyrics')

        if not suno_url or not original_lyrics:
            logging.error("缺少必要参数")
            return jsonify({
                'success': False,
                'message': '请提供完整的参数'
            }), 400

        try:
            api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJKSyIsIlVzZXJOYW1lIjoiSksiLCJBY2NvdW50IjoiIiwiU3ViamVjdElEIjoiMTg2MjA3MDMyNzczNjAyNTEwMCIsIlBob25lIjoiMTMxMTY3OTM3MjUiLCJHcm91cElEIjoiMTg2MjA3MDMyNzczMTgzMDc5NiIsIlBhZ2VOYW1lIjoiIiwiTWFpbCI6IiIsIkNyZWF0ZVRpbWUiOiIyMDI0LTEyLTEwIDExOjI1OjI1IiwiVG9rZW5UeXBlIjoxLCJpc3MiOiJtaW5pbWF4In0.Xheo0uYyQT_RezMZIncWqHKWhjJMP3nBoMgrW_A7gVCCvMUfsG0fExsjjGeAowt6AqVKaHLNLlTwB6nKEXBoYqymwdDBLa57Amd8vPLnYRBw1ql4pv3pVUkPAhAIACSkLS4Oqziz9XEFiLUARt6gR5kWknuzctSKVNsYZHnN0Yky5dwuNTXNr7Mpfcx9yc7Wk-VRvdSACsdBNw5FrCiJYzSN5nFddUUCv-HNxqgPN8fpfV2fgjSLpCy_hjvUF_woVm8MqXtAz-GVtJVOYLp84YJBscZo7qQSWyYDFsavRfyBkdXQQJTLq0Yoohr_WHgjBxBd-6PRrjOze4zSPap71g"
            group_id = "1862070327731830796"
            
            generator = MusicGenerator(api_key=api_key)
            polisher = LyricsPolisher(api_key=api_key, group_id=group_id)

            # 1. 下载音频
            logging.info("开始下载音频")
            downloaded_file = await generator.download_suno_audio(suno_url)
            if not downloaded_file:
                logging.error("音频下载失败")
                return jsonify({
                    'success': False,
                    'message': '音频下载失败'
                }), 500

            logging.info(f"音频下载成功: {downloaded_file}")

            # 2. 润色歌词
            logging.info("开始润色歌词")
            polished_lyrics = await polisher.polish_lyrics(original_lyrics)
            if not polished_lyrics:
                logging.error("歌词润色失败")
                return jsonify({
                    'success': False,
                    'message': '歌词润色失败'
                }), 500
            logging.info(f"歌词润色成功: {polished_lyrics}")

            # 3. 生成音乐，使用润色后的歌词
            logging.info("开始生成音乐")
            output_file = generator.generate_music(
                voice_path=downloaded_file,
                lyrics=polished_lyrics  # 使用润色后的歌词
            )

            if not output_file:
                logging.error("音乐生成失败")
                return jsonify({
                    'success': False,
                    'message': '音乐生成失败'
                }), 500

            # 返回结果
            audio_url = f'/audio/{os.path.basename(output_file)}'
            return jsonify({
                'success': True,
                'audio_url': audio_url,
                'polished_lyrics': polished_lyrics  # 返回润色后的歌词
            })

        except Exception as task_error:
            logging.error(f"任务执行过程中发生错误: {str(task_error)}")
            logging.error(f"错误类型: {type(task_error)}")
            logging.error(f"错误详情: ", exc_info=True)
            raise task_error

    except Exception as e:
        logging.error(f"处理请求时发生错误: {str(e)}")
        logging.error("完整错误信息: ", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"错误: {str(e)}"
        }), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """提供音频文件下载"""
    try:
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logging.error(f"提供音频文件时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '文件不存在'
        }), 404

# 修改 main 函数以支持异步
def main():
    # 确保必要的目录存在
    os.makedirs('static', exist_ok=True)
    os.makedirs('downloads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    # 启动异步 Flask 服务
    app.run(debug=True, port=5000, use_reloader=False)

if __name__ == "__main__":
    main()