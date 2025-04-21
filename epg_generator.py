import os
import json
import hashlib
import time
from datetime import datetime, timedelta
import requests
import pytz
from xml.etree import ElementTree as ET
from xml.dom import minidom

# 配置参数
CHANNEL_IDS = ["141", "146", "147"]
API_BASE_URL = "https://pubmod.hntv.tv/program/getAuth/vod/originStream/program/"
SECRET_KEY = "6ca114a836ac7d73"
TIMEZONE = pytz.timezone("Asia/Shanghai")

def generate_signature():
    """生成API请求签名"""
    timestamp = int(time.time())
    sign_str = f"{SECRET_KEY}{timestamp}"
    return {
        "timestamp": str(timestamp),
        "sign": hashlib.sha256(sign_str.encode()).hexdigest()
    }

def fetch_channel_data(channel_id):
    """获取单个频道数据（修正时间戳类型）"""
    headers = generate_signature()
    try:
        url = f"{API_BASE_URL}{channel_id}/{headers['timestamp']}"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 关键修正：确保时间戳转换为整数
        channel_data = response.json()
        for program in channel_data['programs']:
            program['beginTime'] = int(program['beginTime'])  # 字符串转整数
            program['endTime'] = int(program['endTime'])
        
        return channel_data
    except Exception as e:
        print(f"频道 {channel_id} 数据获取失败: {str(e)}")
        return None


def convert_timestamp(timestamp):
    """转换Unix时间戳到XMLTV格式"""
    dt = datetime.fromtimestamp(timestamp, tz=TIMEZONE)
    return dt.strftime("%Y%m%d%H%M%S %z")

def generate_epg():
    """生成XMLTV文件"""
    # 创建XML根节点
    tv = ET.Element("tv", attrib={
        "info-name": "by spark",
        "info-url": "https://epg.112114.xyz"
    })

    # 处理所有频道
    for channel_id in CHANNEL_IDS:
        data = fetch_channel_data(channel_id)
        if not data:
            continue

        # 添加频道定义
        channel_elem = ET.SubElement(tv, "channel", id=channel_id)
        ET.SubElement(channel_elem, "display-name", lang="zh").text = data['name']

        # 添加节目单
        for program in data['programs']:
            programme = ET.SubElement(tv, "programme", {
                "channel": channel_id,
                "start": convert_timestamp(program['beginTime']),
                "stop": convert_timestamp(program['endTime'])
            })
            ET.SubElement(programme, "title", lang="zh").text = program['title']

    # 格式化输出
    xml_str = minidom.parseString(ET.tostring(tv)).toprettyxml(indent="  ", encoding="UTF-8")
    
    with open("epg.xml", "wb") as f:
        f.write(xml_str)

if __name__ == "__main__":
    generate_epg()
