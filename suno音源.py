import requests
from bs4 import BeautifulSoup
import json
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('suno_downloader.log'),
        logging.StreamHandler()
    ]
)

class SunoDownloader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def download_audio(self, url, output_dir='downloads'):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            logging.info(f"开始下载音频: {url}")
            
            # 从URL中提取音频ID
            song_id = url.split('/')[-1]
            # 构建实际的音频URL
            audio_url = f"https://cdn1.suno.ai/{song_id}.mp3"
            
            # 更新请求头，模拟真实浏览器请求
            self.headers.update({
                'Accept-Encoding': 'identity;q=1, *;q=0',
                'Range': 'bytes=0-',  # 支持断点续传
                'Referer': 'https://suno.com/',
                'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A_Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Android"',
                'User-Agent': 'Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.109 Safari/537.36 CrKey/1.54.248666'
            })
            
            logging.info(f"开始下载音频文件: {audio_url}")
            
            # 下载音频文件
            response = requests.get(audio_url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            # 获取文件大小
            file_size = int(response.headers.get('Content-Length', 0))
            
            # 生成输出文件名
            output_file = os.path.join(output_dir, f'suno_{song_id}.mp3')
            
            # 使用 stream 方式下载大文件
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logging.info(f"音频下载成功: {output_file}")
            return output_file
            
        except requests.exceptions.RequestException as e:
            logging.error(f"下载请求失败: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"下载过程中发生错误: {str(e)}")
            return None

def main():
    try:
        downloader = SunoDownloader()
        url = "https://suno.com/song/2ff26d77-cf22-4dc5-9efe-6a20a8157312"
        output_file = downloader.download_audio(url)
        
        if output_file:
            print(f"音频已下载到: {output_file}")
        else:
            print("下载失败，请查看日志文件了解详细信息")
            
    except Exception as e:
        logging.error(f"程序执行出错: {str(e)}")
        print("程序执行出错，请查看日志文件了解详细信息")

if __name__ == "__main__":
    main()
