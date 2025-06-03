from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

@app.route('/api/naver')
def get_commute():
    start = request.args.get('start')  # 예: 강남역
    end = request.args.get('end')      # 예: 종각역

    # 1단계: 지오코딩 (주소 → 위도/경도)
    geo_url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    geo_headers = {
        "X-NCP-APIGW-API-KEY-ID": CLIENT_ID,
        "X-NCP-APIGW-API-KEY": CLIENT_SECRET
    }
    res_start = requests.get(geo_url, headers=geo_headers, params={"query": start})
    res_end = requests.get(geo_url, headers=geo_headers, params={"query": end})

    coord_start = res_start.json()['addresses'][0]
    coord_end = res_end.json()['addresses'][0]

    sx, sy = coord_start['x'], coord_start['y']
    ex, ey = coord_end['x'], coord_end['y']

    # 2단계: 경로 탐색 API 호출
    dir_url = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving"
    dir_params = {
        "start": f"{sx},{sy};출발지",
        "goal": f"{ex},{ey};도착지"
    }
    res_route = requests.get(dir_url, headers=geo_headers, params=dir_params)
    data = res_route.json()

    summary = data['route']['traoptimal'][0]['summary']

    return jsonify({
        "pt_time": int(summary['duration'] / 60000),  # ms → 분
        "pt_cost": summary['tollFare'],               # 유료도로 비용
        "pt_walk": 0,                                 # 현재는 없음
        "pt_transfer": 0                              # 대중교통 아님
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))  # Render에서 포트 자동 할당
    app.run(host="0.0.0.0", port=port)
