from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

@app.route('/api/naver')
def get_commute():
    try:
        start = request.args.get('start')
        end = request.args.get('end')

        if not start or not end:
            return jsonify({"error": "출발지 또는 도착지 입력이 누락되었습니다."}), 400

        # ===== 1단계: 지오코딩 (주소 → 위도/경도) =====
        geo_url = "https://maps.apigw.ntruss.com/map-geocode/v2/geocode"
        geo_headers = {
            "X-NCP-APIGW-API-KEY-ID": CLIENT_ID,
            "X-NCP-APIGW-API-KEY": CLIENT_SECRET,
            "Accept": "application/json"
        }

        res_start = requests.get(geo_url, headers=geo_headers, params={"query": start})
        res_end = requests.get(geo_url, headers=geo_headers, params={"query": end})

        data_start = res_start.json()
        data_end = res_end.json()

        if not data_start.get('addresses') or not data_end.get('addresses'):
            return jsonify({"error": "지오코딩 실패: 주소를 찾을 수 없습니다."}), 400

        sx = data_start['addresses'][0]['x']
        sy = data_start['addresses'][0]['y']
        ex = data_end['addresses'][0]['x']
        ey = data_end['addresses'][0]['y']

        # ===== 2단계: 경로 탐색 =====
        dir_url = "https://maps.apigw.ntruss.com/map-direction-15/v1/driving"
        dir_params = {
            "start": f"{sx},{sy}",
            "goal": f"{ex},{ey}",
            "option": "traoptimal"
        }

        res_route = requests.get(dir_url, headers=geo_headers, params=dir_params)
        data = res_route.json()

        if data.get("code") != 0:
            return jsonify({"error": f"경로 탐색 실패: {data.get('message', '알 수 없는 오류')}"}), 500

        summary = data['route']['traoptimal'][0]['summary']

        return jsonify({
            "pt_time": int(summary['duration'] / 60000),  # 밀리초 → 분
            "pt_cost": summary.get('tollFare', 0),         # 유료도로 비용
            "pt_walk": 0,                                   # 해당 API엔 도보 없음
            "pt_transfer": 0                                # 대중교통 아님
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
