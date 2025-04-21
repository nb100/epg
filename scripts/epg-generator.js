const CryptoJS = require('crypto-js');
const { create } = require('xmlbuilder2');
const axios = require('axios');
const { format } = require('date-fns');
const { utcToZonedTime } = require('date-fns-tz');

// 配置参数
const CHANNEL_IDS = ["141", "146", "147"];
const API_BASE = 'https://pubmod.hntv.tv/program/getAuth/vod/originStream/program/';
const SECRET = '6ca114a836ac7d73';

// 生成签名请求头
function generateHeaders() {
  const t = Math.floor(Date.now() / 1000);
  const signStr = SECRET + t;
  const sign = CryptoJS.SHA256(signStr).toString(CryptoJS.enc.Hex);
  return { 
    headers: { 
      'timestamp': t.toString(),
      'sign': sign 
    }
  };
}

// 获取单个频道数据
async function fetchChannelData(channelId) {
  try {
    const url = `${API_BASE}${channelId}/${Math.floor(Date.now() / 1000)}`;
    const response = await axios.get(url, generateHeaders());
    
    return {
      id: channelId,
      name: response.data.name,
      programs: response.data.programs.map(p => ({
        title: p.title,
        start: p.beginTime,
        end: p.endTime
      }))
    };
  } catch (error) {
    console.error(`频道 ${channelId} 数据获取失败:`, error.message);
    return null;
  }
}

// 生成XMLTV格式时间
function formatXmlTime(timestamp) {
  const date = new Date(timestamp * 1000); // 添加时间转换
  const zonedDate = utcToZonedTime(date, 'Asia/Shanghai');
  return format(zonedDate, 'yyyyMMddHHmmss') + ' +0800';
}

// 生成EPG XML
async function generateEpg() {
  // 获取所有频道数据
  const channels = await Promise.all(
    CHANNEL_IDS.map(id => fetchChannelData(id))
  ).then(results => results.filter(Boolean));

  // 构建XML
  const root = create({ version: '1.0', encoding: 'UTF-8' })
    .ele('tv', { 'info-name': 'by spark', 'info-url': 'https://epg.112114.xyz' });

  // 添加频道定义
  channels.forEach(channel => {
    root.ele('channel', { id: channel.id })
      .ele('display-name', { lang: 'zh' }).txt(channel.name).up();
  });

  // 添加节目单
  channels.forEach(channel => {
    channel.programs.forEach(program => {
      root.ele('programme', {
        channel: channel.id,
        start: formatXmlTime(program.start),
        stop: formatXmlTime(program.end)
      }).ele('title', { lang: 'zh' }).txt(program.title);
    });
  });

  // 写入文件
  const xml = root.end({ prettyPrint: true });
  require('fs').writeFileSync('epg.xml', xml);
}

// 执行生成
generateEpg();
