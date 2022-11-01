from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, StickerSendMessage, ImageSendMessage, CarouselTemplate, ImageCarouselTemplate, ImageCarouselColumn, PostbackAction, URIAction, MessageAction, TemplateSendMessage, ButtonsTemplate, URITemplateAction, MessageTemplateAction, PostbackTemplateAction, CarouselColumn, ConfirmTemplate
import requests, json, time, statistics

app = Flask(__name__)

access_token = 'IjdKE9zJ3UbdOtB1MSX11aaVNMUUTUymvLvVDOCZXrKaL/B8JDXeOq4KgySShnydrjCD7j3fr74FxQU4If4N2WsmQgKelboqYCYb6mv5cP5En0bwE3/u+BbPYVRmLAcaOXuFsyKFuj4yuMhI8lHXyAdB04t89/1O/w1cDnyilFU='
channel_secret = '852a63927a418a50cc072b35c538e3e0'

@app.route("/callback", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)
    try:
        line_bot_api = LineBotApi(access_token)
        handler = WebhookHandler(channel_secret)
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)
        json_data = json.loads(body)
        reply_token = json_data['events'][0]['replyToken']
        user_id = json_data['events'][0]['source']['userId']
        print(json_data)
        if 'message' in json_data['events'][0]:
            if json_data['events'][0]['message']['type'] == 'location':
                address = json_data['events'][0]['message']['address'].replace('台','臺')
                # 回覆爬取到的相關氣象資訊
                reply_message(f'{address}\n\n{current_weather(address)}\n\n{aqi(address)}\n\n{forecast(address)}', reply_token, access_token)
                print(address)
            if json_data['events'][0]['message']['type'] == 'text':
                text = json_data['events'][0]['message']['text']
                if text == '雷達回波' or text == '雷達':
                    reply_image(f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png?{time.time_ns()}', reply_token, access_token)
                if text == '即時溫度' or text == '溫度':
                    reply_image(f'https://www.cwb.gov.tw/Data/temperature/temp.jpg?{time.time_ns()}', reply_token, access_token)    
                elif text == '地震資訊' or text == '地震':              # 如果是地震相關的文字
                    msg = earth_quake()                               # 爬取地震資訊
                    push_message(msg[0], user_id, access_token)       # 傳送地震資訊 ( 用 push 方法，因為 reply 只能用一次 )
                    reply_image(msg[1], reply_token, access_token)    # 傳送地震圖片 ( 用 reply 方法 )
                elif text == '回波動態圖' or text == '動態圖':
                    reply_image(f'https://watch.ncdr.nat.gov.tw/00_Wxmap/5A8_DBZ_TRACK/dbztracks.gif', reply_token, access_token)
                elif text == '文字' or text == 'text':
                    line_bot_api.reply_message(reply_token, TextSendMessage(text='002Hello World!'))
                elif text == 'sticker' or text == '貼圖':
                    line_bot_api.reply_message(reply_token, StickerSendMessage(package_id=1, sticker_id=2))
                elif text == 'pic' or text == '圖片':
                    line_bot_api.reply_message(reply_token,ImageSendMessage(original_content_url='https://cdn-icons-png.flaticon.com/512/685/685842.png', preview_image_url='https://cdn-icons-png.flaticon.com/512/685/685842.png'))
                elif text == 'test' or text == '即時天氣':  
                    confirm_template_message = TemplateSendMessage(
    alt_text='Carousel template',
    template=CarouselTemplate(
        columns=[
            CarouselColumn(
                thumbnail_image_url='https://i.imgur.com/40ejOWi.jpeg',
                title='即時天氣資訊',
                text='',
                actions=[
                    PostbackAction(
                        label='雷達回波',
                        display_text='雷達回波',
                        data='action=buy&itemid=1'
                    ),
                    MessageAction(
                        label='回波動態圖',
                        text='回波動態圖'
                    ),
                    MessageAction(
                        label='溫度分布圖',
                        text='溫度分布圖'
                    )
                ]
            ),
            CarouselColumn(
                thumbnail_image_url='https://i.imgur.com/40ejOWi.jpeg',
                title='this is menu2',
                text='description2',
                actions=[
                    PostbackAction(
                        label='累積雨量',
                        display_text='累積雨量',
                        data='action=buy&itemid=2'
                    ),
                    MessageAction(
                        label='地震資訊',
                        text='地震資訊'
                    ),
                    MessageAction(
                        label='test',
                        text='test'
                    )
                ]
            )
        ]
    )
)
                    line_bot_api.reply_message(reply_token, confirm_template_message)
                else:
                    reply_message(f'無效的指令', reply_token, access_token)    # 如果是一般文字，直接回覆 無效的指令
    except:
        print('error')
    return 'OK'

if __name__ == "__main__":
  app.run()


# 地震資訊函式
def earth_quake():
    msg = ['找不到地震資訊','https://example.com/demo.jpg']            # 預設回傳的訊息
    try:
        code = 'CWB-303281A4-9D52-4BB3-A5E0-18A742D834CE'    #你的氣象資料授權碼
        url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={code}'
        e_data = requests.get(url)                                   # 爬取地震資訊網址
        e_data_json = e_data.json()                                  # json 格式化訊息內容
        eq = e_data_json['records']['earthquake']                    # 取出地震資訊
        for i in eq:
            loc = i['earthquakeInfo']['epiCenter']['location']       # 地震地點
            val = i['earthquakeInfo']['magnitude']['magnitudeValue'] # 地震規模
            dep = i['earthquakeInfo']['depth']['value']              # 地震深度
            eq_time = i['earthquakeInfo']['originTime']              # 地震時間
            img = i['reportImageURI']                                # 地震圖
            msg = [f'{loc}，芮氏規模 {val} 級，深度 {dep} 公里，發生時間 {eq_time}。', img]
            break     # 取出第一筆資料後就 break
        return msg    # 回傳 msg
    except:
        return msg    # 如果取資料有發生錯誤，直接回傳 msg

    
# LINE push 訊息函式
def push_message(msg, uid, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}   
    body = {
    'to':uid,
    'messages':[{
            "type": "text",
            "text": msg
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/push', headers=headers,data=json.dumps(body).encode('utf-8'))
    print(req.text)

    
# LINE 回傳訊息函式
def reply_message(msg, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {
    'replyToken':rk,
    'messages':[{
            "type": "text",
            "text": msg
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    print(req.text)

    
# LINE 回傳圖片函式
def reply_image(msg, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
    body = {
    'replyToken':rk,
    'messages':[{
          'type': 'image',
          'originalContentUrl': msg,
          'previewImageUrl': msg
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    req.raise_for_status()
    print(req.text)



# 目前天氣函式
def current_weather(address):
    city_list, area_list, area_list2 = {}, {}, {} # 定義好待會要用的變數
    msg = '找不到氣象資訊。'                         # 預設回傳訊息

    # 定義取得資料的函式
    def get_data(url):
        w_data = requests.get(url)   # 爬取目前天氣網址的資料
        w_data_json = w_data.json()  # json 格式化訊息內容
        location = w_data_json['cwbopendata']['location']  # 取出對應地點的內容
        for i in location:
            name = i['locationName']                       # 測站地點
            city = i['parameter'][0]['parameterValue']     # 縣市名稱
            area = i['parameter'][2]['parameterValue']     # 鄉鎮行政區
            temp = check_data(i['weatherElement'][3]['elementValue']['value'])                       # 氣溫
            humd = check_data(round(float(i['weatherElement'][4]['elementValue']['value'] )*100 ,1)) # 相對濕度
            r24 = check_data(i['weatherElement'][6]['elementValue']['value'])                        # 累積雨量
            if area not in area_list:
                area_list[area] = {'temp':temp, 'humd':humd, 'r24':r24}  # 以鄉鎮區域為 key，儲存需要的資訊
            if city not in city_list:
                city_list[city] = {'temp':[], 'humd':[], 'r24':[]}       # 以主要縣市名稱為 key，準備紀錄裡面所有鄉鎮的數值
            city_list[city]['temp'].append(temp)   # 記錄主要縣市裡鄉鎮區域的溫度 ( 串列格式 )
            city_list[city]['humd'].append(humd)   # 記錄主要縣市裡鄉鎮區域的濕度 ( 串列格式 )
            city_list[city]['r24'].append(r24)     # 記錄主要縣市裡鄉鎮區域的雨量 ( 串列格式 )

    # 定義如果數值小於 0，回傳 False 的函式
    def check_data(e):
        return False if float(e)<0 else float(e)

    # 定義產生回傳訊息的函式
    def msg_content(loc, msg):
        a = msg
        for i in loc:
            if i in address: # 如果地址裡存在 key 的名稱
                temp = f"氣溫 {loc[i]['temp']} 度，" if loc[i]['temp'] != False else ''
                humd = f"相對濕度 {loc[i]['humd']}%，" if loc[i]['humd'] != False else ''
                r24 = f"累積雨量 {loc[i]['r24']}mm" if loc[i]['r24'] != False else ''
                description = f'{temp}{humd}{r24}'.strip('，')
                a = f'{description}。' # 取出 key 的內容作為回傳訊息使用
                break
        return a

    try:
        # 因為目前天氣有兩組網址，兩組都爬取
        code = 'CWB-303281A4-9D52-4BB3-A5E0-18A742D834CE'
        get_data(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0001-001?Authorization={code}&downloadType=WEB&format=JSON')
        #get_data(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0003-001?Authorization={code}&downloadType=WEB&format=JSON')

        for i in city_list:
            if i not in area_list2: # 將主要縣市裡的數值平均後，以主要縣市名稱為 key，再度儲存一次，如果找不到鄉鎮區域，就使用平均數值
                area_list2[i] = {'temp':round(statistics.mean(city_list[i]['temp']),1),
                                'humd':round(statistics.mean(city_list[i]['humd']),1),
                                'r24':round(statistics.mean(city_list[i]['r24']),1)
                                }
        msg = msg_content(area_list2, msg)  # 將訊息改為「大縣市」
        msg = msg_content(area_list, msg)   # 將訊息改為「鄉鎮區域」
        return msg    # 回傳 msg
    except:
        return msg    # 如果取資料有發生錯誤，直接回傳 msg        
        
        
        
        
# ######   氣象預報函式 #######
def forecast(address):
    area_list = {}
    # 將主要縣市個別的 JSON 代碼列出
    json_api = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}
    msg = '找不到天氣預報資訊。'    # 預設回傳訊息
    try:
        code = 'CWB-303281A4-9D52-4BB3-A5E0-18A742D834CE'     #你的氣象開放平台授權碼
        url = f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization={code}&downloadType=WEB&format=JSON'
        f_data = requests.get(url)   # 取得主要縣市預報資料
        f_data_json = f_data.json()  # json 格式化訊息內容
        location = f_data_json['cwbopendata']['dataset']['location']  # 取得縣市的預報內容
        for i in location:
            city = i['locationName']    # 縣市名稱
            wx8 = i['weatherElement'][0]['time'][0]['parameter']['parameterName']    # 天氣現象
            mint8 = i['weatherElement'][1]['time'][0]['parameter']['parameterName']  # 最低溫
            maxt8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']  # 最高溫
            ci8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']    # 舒適度
            pop8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']   # 降雨機率
            area_list[city] = f'未來 8 小時{wx8}，最高溫 {maxt8} 度，最低溫 {mint8} 度，降雨機率 {pop8} %'  # 組合成回傳的訊息，存在以縣市名稱為 key 的字典檔裡
        for i in area_list:
            if i in address:        # 如果使用者的地址包含縣市名稱
                msg = area_list[i]  # 將 msg 換成對應的預報資訊
                # 將進一步的預報網址換成對應的預報網址
                url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/{json_api[i]}?Authorization={code}&elementName=WeatherDescription'
                f_data = requests.get(url)  # 取得主要縣市裡各個區域鄉鎮的氣象預報
                f_data_json = f_data.json() # json 格式化訊息內容
                location = f_data_json['records']['locations'][0]['location']    # 取得預報內容
                break
        for i in location:
            city = i['locationName']   # 取得縣市名稱
            wd = i['weatherElement'][0]['time'][1]['elementValue'][0]['value']  # 綜合描述
            if city in address:           # 如果使用者的地址包含鄉鎮區域名稱
                msg = f'未來八小時天氣{wd}' # 將 msg 換成對應的預報資訊
                break
        return msg  # 回傳 msg
    except:
        return msg  # 如果取資料有發生錯誤，直接回傳 msg
    
    
    #####    空氣品質函式 ######
def aqi(address):
    city_list, site_list ={}, {}
    msg = '找不到空氣品質資訊。'
    try:
        url = 'https://data.epa.gov.tw/api/v2/aqx_p_432?api_key=24d195ca-27e8-4217-9368-b4c4c65fe56a&limit=1000&sort=ImportDate%20desc&format=json'
        a_data = requests.get(url)             # 使用 get 方法透過空氣品質指標 API 取得內容
        a_data_json = a_data.json()            # json 格式化訊息內容
        for i in a_data_json['records']:       # 依序取出 records 內容的每個項目
            city = i['County']                 # 取出縣市名稱
            if city not in city_list:
                city_list[city]=[]             # 以縣市名稱為 key，準備存入串列資料
            site = i['SiteName']               # 取出鄉鎮區域名稱
            aqi = int(i['AQI'])                # 取得 AQI 數值
            status = i['Status']               # 取得空氣品質狀態
            site_list[site] = {'aqi':aqi, 'status':status}  # 記錄鄉鎮區域空氣品質
            city_list[city].append(aqi)        # 將各個縣市裡的鄉鎮區域空氣 aqi 數值，以串列方式放入縣市名稱的變數裡
        for i in city_list:
            if i in address: # 如果地址裡包含縣市名稱的 key，就直接使用對應的內容
                # 參考 https://airtw.epa.gov.tw/cht/Information/Standard/AirQualityIndicator.aspx
                aqi_val = round(statistics.mean(city_list[i]),0)  # 計算平均數值，如果找不到鄉鎮區域，就使用縣市的平均值
                aqi_status = ''  # 手動判斷對應的空氣品質說明文字
                if aqi_val<=50: aqi_status = '良好'
                elif aqi_val>50 and aqi_val<=100: aqi_status = '普通'
                elif aqi_val>100 and aqi_val<=150: aqi_status = '對敏感族群不健康'
                elif aqi_val>150 and aqi_val<=200: aqi_status = '對所有族群不健康'
                elif aqi_val>200 and aqi_val<=300: aqi_status = '非常不健康'
                else: aqi_status = '危害'
                msg = f'空氣品質{aqi_status} ( AQI {aqi_val} )。' # 定義回傳的訊息
                break
        for i in site_list:
            if i in address:  # 如果地址裡包含鄉鎮區域名稱的 key，就直接使用對應的內容
                msg = f'空氣品質{site_list[i]["status"]} ( AQI {site_list[i]["aqi"]} )。'
                break
        return msg    # 回傳 msg
    except:
        return msg    # 如果取資料有發生錯誤，直接回傳 msg
